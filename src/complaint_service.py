"""
Service for processing complaints - classification and similarity search
"""
import os
import json
from datetime import datetime
from typing import Optional, List, Dict
from database import db


class ComplaintService:
    """Service to handle complaint processing"""

    def __init__(self, classifier=None, search_engine=None, vllm_service=None, classification_service=None, case_service=None):
        """
        Initialize complaint service with AI models

        Args:
            classifier: SPRM Classifier instance (legacy)
            search_engine: Case Search Engine instance
            vllm_service: VLLM Service instance for extraction and 5W1H
            classification_service: Classification service for CRIS/NFA
            case_service: Case service for auto-grouping
        """
        self.classifier = classifier
        self.search_engine = search_engine
        self.vllm_service = vllm_service
        self.classification_service = classification_service
        self.case_service = case_service

    def save_complaint(self, complaint_data: Dict) -> int:
        """
        Save complaint to database
        All complainant fields are optional (allows anonymous complaints)

        Args:
            complaint_data: Dictionary with complaint information

        Returns:
            complaint_id: ID of inserted complaint
        """
        query = """
        INSERT INTO complaints (
            full_name, ic_number, phone_number, email,
            complaint_title, complaint_description,
            status
        ) VALUES (
            %(full_name)s, %(ic_number)s, %(phone_number)s, %(email)s,
            %(complaint_title)s, %(complaint_description)s,
            'pending'
        ) RETURNING id
        """

        with db.get_cursor() as cursor:
            cursor.execute(query, complaint_data)
            result = cursor.fetchone()
            return result['id']

    def save_document(self, complaint_id: int, filename: str, original_filename: str,
                     file_path: str, file_size: int, file_type: str) -> int:
        """
        Save document metadata to database

        Args:
            complaint_id: ID of the complaint
            filename: Stored filename
            original_filename: Original uploaded filename
            file_path: Path where file is stored
            file_size: Size of file in bytes
            file_type: MIME type of file

        Returns:
            document_id: ID of inserted document
        """
        query = """
        INSERT INTO complaint_documents (
            complaint_id, filename, original_filename, file_path, file_size, file_type
        ) VALUES (
            %s, %s, %s, %s, %s, %s
        ) RETURNING id
        """

        with db.get_cursor() as cursor:
            cursor.execute(query, (complaint_id, filename, original_filename,
                                  file_path, file_size, file_type))
            result = cursor.fetchone()
            return result['id']

    def update_document_count(self, complaint_id: int, count: int):
        """Update document count for complaint"""
        query = """
        UPDATE complaints
        SET has_documents = TRUE, document_count = %s
        WHERE id = %s
        """
        with db.get_cursor() as cursor:
            cursor.execute(query, (count, complaint_id))

    def classify_complaint(self, complaint_id: int) -> Optional[Dict]:
        """
        Classify a complaint using the AI classifier

        Args:
            complaint_id: ID of complaint to classify

        Returns:
            Dictionary with classification results or None if classifier unavailable
        """
        if not self.classifier or not self.classifier.classifier:
            print(f"⚠️  Classifier not available for complaint {complaint_id}")
            return None

        # Get complaint text
        query = """
        SELECT complaint_title, complaint_description, category
        FROM complaints
        WHERE id = %s
        """

        with db.get_cursor() as cursor:
            cursor.execute(query, (complaint_id,))
            complaint = cursor.fetchone()

        if not complaint:
            return None

        # Combine text fields for classification
        combined_text = f"{complaint['complaint_title']}. {complaint['complaint_description']}"

        try:
            # Classify
            result = self.classifier.predict(combined_text)

            # Update database
            update_query = """
            UPDATE complaints
            SET classification = %s,
                classification_confidence = %s,
                status = 'classified',
                processed_at = CURRENT_TIMESTAMP
            WHERE id = %s
            """

            with db.get_cursor() as cursor:
                cursor.execute(update_query, (
                    result['classification'],
                    result['confidence'],
                    complaint_id
                ))

            print(f"✅ Complaint {complaint_id} classified as {result['classification']} ({result['confidence']:.2f}%)")
            return result

        except Exception as e:
            print(f"❌ Error classifying complaint {complaint_id}: {e}")
            return None

    def find_similar_cases(self, complaint_id: int, top_k: int = 5) -> Optional[List[Dict]]:
        """
        Find similar cases for a complaint

        Args:
            complaint_id: ID of complaint
            top_k: Number of similar cases to find

        Returns:
            List of similar cases or None if search engine unavailable
        """
        if not self.search_engine or not self.search_engine.cases:
            print(f"⚠️  Search engine not available for complaint {complaint_id}")
            return None

        # Get complaint text
        query = """
        SELECT complaint_title, complaint_description, category
        FROM complaints
        WHERE id = %s
        """

        with db.get_cursor() as cursor:
            cursor.execute(query, (complaint_id,))
            complaint = cursor.fetchone()

        if not complaint:
            return None

        # Combine text for search
        search_text = f"{complaint['complaint_title']}. {complaint['complaint_description']}"

        try:
            # Search for similar cases
            query_desc = {'description': search_text}
            results = self.search_engine.search(query_description=query_desc, top_k=top_k)

            # Save similar cases to database
            for result in results:
                insert_query = """
                INSERT INTO similar_cases (
                    complaint_id, similar_case_id, similarity_score, rank
                ) VALUES (%s, %s, %s, %s)
                """

                with db.get_cursor() as cursor:
                    cursor.execute(insert_query, (
                        complaint_id,
                        result['id'],
                        result['similarity_score'],
                        result['rank']
                    ))

            print(f"✅ Found {len(results)} similar cases for complaint {complaint_id}")
            return results

        except Exception as e:
            print(f"❌ Error finding similar cases for complaint {complaint_id}: {e}")
            return None

    def process_complaint(self, complaint_id: int) -> Dict:
        """
        Process a complaint - classify and find similar cases

        Args:
            complaint_id: ID of complaint to process

        Returns:
            Dictionary with processing results
        """
        results = {
            'complaint_id': complaint_id,
            'classification': None,
            'similar_cases': None,
            'status': 'submitted'
        }

        # Classify
        classification_result = self.classify_complaint(complaint_id)
        if classification_result:
            results['classification'] = classification_result
            results['status'] = 'classified'
        else:
            print(f"ℹ️  Skipping classification for complaint {complaint_id} (model not ready)")

        # Find similar cases
        similar_cases = self.find_similar_cases(complaint_id)
        if similar_cases:
            results['similar_cases'] = similar_cases
            # Only mark as processed if we got similar cases
            if results['status'] == 'classified':
                results['status'] = 'processed'
        else:
            print(f"ℹ️  Skipping similarity search for complaint {complaint_id} (search engine not ready)")

        # Update final status
        # If neither worked, status stays as 'submitted'
        # If only classification worked, status is 'classified'
        # If both worked, status is 'processed'
        update_query = """
        UPDATE complaints
        SET status = %s
        WHERE id = %s
        """

        with db.get_cursor() as cursor:
            cursor.execute(update_query, (results['status'], complaint_id))

        return results

    def get_complaint(self, complaint_id: int) -> Optional[Dict]:
        """Get complaint details by ID"""
        query = """
        SELECT * FROM complaints WHERE id = %s
        """

        with db.get_cursor() as cursor:
            cursor.execute(query, (complaint_id,))
            return cursor.fetchone()

    def get_complaint_documents(self, complaint_id: int) -> List[Dict]:
        """Get all documents for a complaint"""
        query = """
        SELECT * FROM complaint_documents WHERE complaint_id = %s
        """

        with db.get_cursor() as cursor:
            cursor.execute(query, (complaint_id,))
            return cursor.fetchall()

    def get_similar_cases(self, complaint_id: int) -> List[Dict]:
        """Get similar cases for a complaint"""
        query = """
        SELECT * FROM similar_cases WHERE complaint_id = %s ORDER BY rank
        """

        with db.get_cursor() as cursor:
            cursor.execute(query, (complaint_id,))
            return cursor.fetchall()

    def process_vllm_extraction(self, complaint_id: int) -> Optional[Dict]:
        """
        Process complaint through VLLM API for data extraction and 5W1H generation

        Args:
            complaint_id: ID of complaint to process

        Returns:
            Dictionary with extraction results or None if failed
        """
        if not self.vllm_service:
            print(f"⚠️  VLLM service not available for complaint {complaint_id}")
            return None

        # Get complaint text
        query = """
        SELECT complaint_title, complaint_description
        FROM complaints
        WHERE id = %s
        """

        with db.get_cursor() as cursor:
            cursor.execute(query, (complaint_id,))
            complaint = cursor.fetchone()

        if not complaint:
            return None

        # Get uploaded documents
        documents = self.get_complaint_documents(complaint_id)
        document_paths = [doc['file_path'] for doc in documents] if documents else []

        # Combine text for processing
        complaint_text = f"{complaint['complaint_title']}\n\n{complaint['complaint_description']}"

        try:
            # Call VLLM service for extraction and 5W1H (with documents!)
            print(f"🔄 Processing complaint {complaint_id} with {len(document_paths)} document(s)")
            result = self.vllm_service.process_complaint_with_vllm(
                complaint_text=complaint_text,
                document_paths=document_paths
            )

            if result.get('success'):
                # Step 1: Classify based on 5W1H summary
                classification_result = None
                if result.get('w1h_summary') and self.classification_service:
                    print(f"🔍 Classifying complaint {complaint_id} based on 5W1H...")
                    classification_result = self.classification_service.classify_from_5w1h(
                        w1h_summary=result['w1h_summary'],
                        complaint_description=complaint['complaint_description']
                    )
                    result['classification'] = classification_result

                # Step 2: Generate sector and sub-sector
                sector = None
                sub_sector = None
                if result.get('w1h_summary'):
                    print(f"🏢 Determining sector and sub-sector for complaint {complaint_id}...")
                    sector_result = self.vllm_service.generate_sector_and_subsector(
                        w1h_summary=result['w1h_summary'],
                        complaint_text=complaint_text
                    )
                    if sector_result:
                        sector = sector_result['sector']
                        sub_sector = sector_result['sub_sector']
                        result['sector'] = sector
                        result['sub_sector'] = sub_sector
                    else:
                        print(f"⚠️  Sector/sub-sector generation failed, using fallback")
                        result['sector'] = None
                        result['sub_sector'] = None

                # Step 3: Generate akta (legislation) using two-step category approach
                akta = None
                if result.get('w1h_summary'):
                    print(f"⚖️  Determining akta for complaint {complaint_id}...")
                    # Try to load akta simple service
                    akta_service = None
                    try:
                        from akta_simple_service import AktaSimpleService
                        akta_service = AktaSimpleService()
                    except Exception as e:
                        print(f"⚠️  Could not load AktaSimpleService: {e}")

                    akta = self.vllm_service.generate_akta(
                        w1h_summary=result['w1h_summary'],
                        complaint_text=complaint_text,
                        sector=sector,
                        akta_service=akta_service
                    )
                    result['akta'] = akta

                # Step 3.5: Generate executive summary
                summary = None
                if result.get('w1h_summary') or result.get('extracted_data'):
                    print(f"📄 Generating executive summary for complaint {complaint_id}...")
                    complaint_form_data = {
                        'complaint_title': complaint['complaint_title'],
                        'complaint_description': complaint['complaint_description'],
                        'category': complaint.get('category'),
                        'urgency_level': complaint.get('urgency_level')
                    }
                    summary = self.vllm_service.generate_complaint_summary(
                        complaint_data=complaint_form_data,
                        extracted_data=result.get('extracted_data'),
                        w1h_summary=result.get('w1h_summary')
                    )
                    result['summary'] = summary

                # Step 4: Generate embedding for similarity search
                embedding = None
                if result.get('w1h_summary'):
                    print(f"🔢 Generating embedding for complaint {complaint_id}...")
                    try:
                        # Get search engine for embedding generation
                        from search_relevant_case import CaseSearchEngine
                        search_engine = CaseSearchEngine()
                        search_engine.load_model()

                        # Create text for embedding from 5W1H + description
                        w1h_text = result['w1h_summary'].get('full_text', '') if isinstance(result['w1h_summary'], dict) else result['w1h_summary']
                        embedding_text = f"{complaint['complaint_title']} {complaint['complaint_description']} {w1h_text}"

                        # Generate embedding
                        embedding_array = search_engine.generate_embedding(embedding_text)
                        embedding = embedding_array.tolist()  # Convert numpy array to list for PostgreSQL
                        result['embedding'] = embedding
                        print(f"✅ Embedding generated ({len(embedding)} dimensions)")
                    except Exception as e:
                        print(f"⚠️  Error generating embedding: {e}")

                # Update database with results (including classification, structured 5W1H, sector, sub-sector, akta, summary, and embedding)
                update_query = """
                UPDATE complaints
                SET extracted_data = %s,
                    w1h_summary = %s,
                    w1h_what = %s,
                    w1h_who = %s,
                    w1h_when = %s,
                    w1h_where = %s,
                    w1h_why = %s,
                    w1h_how = %s,
                    sector = %s,
                    sub_sector = %s,
                    akta = %s,
                    summary = %s,
                    embedding = %s,
                    classification = %s,
                    classification_confidence = %s,
                    status = 'processed',
                    officer_status = 'pending_review',
                    processed_at = CURRENT_TIMESTAMP
                WHERE id = %s
                """

                # Convert extracted_data to JSON string for JSONB column
                extracted_json = json.dumps(result['extracted_data']) if result['extracted_data'] else None

                # Get 5W1H structured fields
                w1h_data = result.get('w1h_summary')
                print(f"   📊 5W1H data type: {type(w1h_data)}")
                if w1h_data:
                    print(f"   📊 5W1H keys: {w1h_data.keys() if isinstance(w1h_data, dict) else 'N/A'}")

                if isinstance(w1h_data, dict):
                    # Structured format
                    w1h_full_text = w1h_data.get('full_text')
                    w1h_what = w1h_data.get('what')
                    w1h_who = w1h_data.get('who')
                    w1h_when = w1h_data.get('when')
                    w1h_where = w1h_data.get('where')
                    w1h_why = w1h_data.get('why')
                    w1h_how = w1h_data.get('how')
                    print(f"   ✅ Structured 5W1H parsed")
                    print(f"      WHAT: {w1h_what[:50] if w1h_what else 'None'}...")
                    print(f"      WHO: {w1h_who[:50] if w1h_who else 'None'}...")
                elif isinstance(w1h_data, str):
                    # Old text format (backward compatibility)
                    w1h_full_text = w1h_data
                    w1h_what = w1h_who = w1h_when = w1h_where = w1h_why = w1h_how = None
                    print(f"   ⚠️  Using text format (backward compatibility)")
                else:
                    w1h_full_text = w1h_what = w1h_who = w1h_when = w1h_where = w1h_why = w1h_how = None
                    print(f"   ❌ No 5W1H data found")

                # Get classification values
                classification_label = classification_result['classification'] if classification_result else None
                classification_conf = classification_result['confidence'] if classification_result else None

                # Get summary
                summary_text = result.get('summary')

                with db.get_cursor() as cursor:
                    cursor.execute(update_query, (
                        extracted_json,
                        w1h_full_text,
                        w1h_what,
                        w1h_who,
                        w1h_when,
                        w1h_where,
                        w1h_why,
                        w1h_how,
                        sector,
                        sub_sector,
                        akta,
                        summary_text,
                        embedding,
                        classification_label,
                        classification_conf,
                        complaint_id
                    ))

                print(f"✅ VLLM processing completed for complaint {complaint_id}")
                print(f"   Documents processed: {len(document_paths)}")
                print(f"   Extracted data: {'Yes' if result['extracted_data'] else 'No'}")
                print(f"   5W1H summary: {'Generated' if result['w1h_summary'] else 'Not generated'}")
                if summary_text:
                    print(f"   Executive summary: Generated ({len(summary_text)} chars)")
                if sector:
                    print(f"   Sector: {sector}")
                if akta:
                    print(f"   Akta: {akta}")
                if classification_result:
                    print(f"   Classification: {classification_result['classification']} ({classification_result['confidence_percentage']:.1f}%)")

                return result
            else:
                print(f"⚠️  VLLM processing failed for complaint {complaint_id}")
                return None

        except Exception as e:
            print(f"❌ Error in VLLM processing for complaint {complaint_id}: {e}")
            import traceback
            traceback.print_exc()
            return None

    def process_complaint_new(self, complaint_id: int) -> Dict:
        """
        New processing pipeline: VLLM extraction + 5W1H + Classification + Case Grouping

        Args:
            complaint_id: ID of complaint to process

        Returns:
            Dictionary with processing results
        """
        results = {
            'complaint_id': complaint_id,
            'extracted_data': None,
            'w1h_summary': None,
            'classification': None,
            'case_id': None,
            'status': 'submitted'
        }

        # Process with VLLM
        vllm_result = self.process_vllm_extraction(complaint_id)
        if vllm_result:
            results['extracted_data'] = vllm_result.get('extracted_data')
            results['w1h_summary'] = vllm_result.get('w1h_summary')
            results['classification'] = vllm_result.get('classification')
            results['status'] = 'processed'

            # Auto-group into case after processing
            if self.case_service:
                print(f"🔗 Auto-grouping complaint {complaint_id} into case...")
                try:
                    case_id = self.case_service.auto_group_complaint(complaint_id)
                    results['case_id'] = case_id
                    if case_id:
                        print(f"✅ Complaint {complaint_id} grouped into case {case_id}")
                except Exception as e:
                    print(f"⚠️  Error auto-grouping complaint: {e}")

        else:
            print(f"ℹ️  VLLM processing not available for complaint {complaint_id}")
            # Update status to submitted if VLLM fails
            update_query = """
            UPDATE complaints
            SET status = 'submitted'
            WHERE id = %s
            """
            with db.get_cursor() as cursor:
                cursor.execute(update_query, (complaint_id,))

        return results
