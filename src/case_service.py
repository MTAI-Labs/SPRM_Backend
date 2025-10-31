"""
Case Management Service
========================
Auto-groups related complaints into cases and provides CRUD operations.

Features:
- Automatic case grouping based on similarity
- Multi-factor similarity: entities, location, timeframe, corruption type
- Manual case management (create, update, move complaints)
- Case title generation from common keywords
"""

import os
import re
from typing import List, Dict, Optional, Any
from datetime import datetime, timedelta
from collections import Counter
from database import db


class CaseService:
    """Service for managing cases and grouping complaints"""

    def __init__(self, search_engine=None):
        """
        Initialize Case Service

        Args:
            search_engine: CaseSearchEngine instance for similarity search
        """
        self.search_engine = search_engine
        self.similarity_threshold = float(os.getenv("CASE_GROUPING_THRESHOLD", "0.70"))
        self.min_similarity_for_auto_group = 0.70  # High confidence threshold

    def generate_case_number(self) -> str:
        """
        Generate unique case number (e.g., CASE-2025-0001)

        Returns:
            Unique case number string
        """
        year = datetime.now().year

        # Get count of cases created this year
        query = """
        SELECT COUNT(*) as count
        FROM cases
        WHERE EXTRACT(YEAR FROM created_at) = %s
        """

        with db.get_cursor() as cursor:
            cursor.execute(query, (year,))
            result = cursor.fetchone()
            count = result['count'] if result else 0

        # Format: CASE-2025-0001
        case_number = f"CASE-{year}-{str(count + 1).zfill(4)}"
        return case_number

    def generate_case_title(self, complaint_titles: List[str]) -> str:
        """
        Generate case title from complaint titles

        Args:
            complaint_titles: List of complaint titles

        Returns:
            Generated case title
        """
        if not complaint_titles:
            return "Untitled Case"

        # If only one complaint, use its title (truncated if too long)
        if len(complaint_titles) == 1:
            title = complaint_titles[0]
            return title[:100] if len(title) > 100 else title

        # Multiple complaints - create generic title with count
        return f"Kes: {len(complaint_titles)} Aduan Berkaitan"

    def find_similar_complaints(self, complaint_id: int, top_k: int = 10) -> List[Dict]:
        """
        Find similar complaints using search engine

        Args:
            complaint_id: Complaint ID to search for
            top_k: Number of similar complaints to return

        Returns:
            List of similar complaints with similarity scores
        """
        if not self.search_engine:
            return []

        # Get complaint data
        complaint = self.get_complaint_by_id(complaint_id)
        if not complaint:
            return []

        # Prepare search query from complaint data
        query_text = complaint.get('complaint_description', '')
        if complaint.get('w1h_summary'):
            query_text = f"{query_text} {complaint['w1h_summary']}"

        # Search for similar complaints
        try:
            results = self.search_engine.search(query_text=query_text, top_k=top_k + 1)

            # Filter out the same complaint and low similarity scores
            similar = []
            for result in results:
                if result.get('id') != complaint_id and result.get('similarity_score', 0) >= self.similarity_threshold:
                    similar.append(result)

            return similar[:top_k]
        except Exception as e:
            print(f"❌ Error searching for similar complaints: {e}")
            return []

    def get_complaint_by_id(self, complaint_id: int) -> Optional[Dict]:
        """Get complaint by ID"""
        query = "SELECT * FROM complaints WHERE id = %s"
        with db.get_cursor() as cursor:
            cursor.execute(query, (complaint_id,))
            return cursor.fetchone()

    def get_case_for_complaint(self, complaint_id: int) -> Optional[Dict]:
        """
        Check if complaint is already in a case

        Args:
            complaint_id: Complaint ID

        Returns:
            Case dictionary or None
        """
        query = """
        SELECT c.*
        FROM cases c
        JOIN case_complaints cc ON c.id = cc.case_id
        WHERE cc.complaint_id = %s
        LIMIT 1
        """

        with db.get_cursor() as cursor:
            cursor.execute(query, (complaint_id,))
            return cursor.fetchone()

    def create_case(self, complaint_ids: List[int], case_title: str = None,
                   auto_grouped: bool = True, added_by: str = 'system',
                   related_cases: List[Dict] = None) -> Optional[int]:
        """
        Create a new case with complaints

        Args:
            complaint_ids: List of complaint IDs to include
            case_title: Optional case title (auto-generated if not provided)
            auto_grouped: Whether case was auto-grouped
            added_by: 'system' or username
            related_cases: List of related closed cases for reference

        Returns:
            Case ID or None if failed
        """
        if not complaint_ids:
            return None

        # Get complaint data for all complaints
        complaints = []
        for cid in complaint_ids:
            complaint = self.get_complaint_by_id(cid)
            if complaint:
                complaints.append(complaint)

        if not complaints:
            return None

        # Generate case number
        case_number = self.generate_case_number()

        # Generate case title if not provided
        if not case_title:
            titles = [c['complaint_title'] for c in complaints]
            case_title = self.generate_case_title(titles)

        # Get most common classification
        classifications = [c.get('classification') for c in complaints if c.get('classification')]
        primary_classification = Counter(classifications).most_common(1)[0][0] if classifications else None

        # Get priority based on urgency levels
        urgencies = [c.get('urgency_level', 'Sederhana') for c in complaints]
        priority_map = {'Rendah': 'low', 'Sederhana': 'medium', 'Tinggi': 'high', 'Kritikal': 'critical'}
        priorities = [priority_map.get(u, 'medium') for u in urgencies]
        primary_priority = max(priorities, key=['low', 'medium', 'high', 'critical'].index)

        # Prepare related_cases JSON
        import json
        related_cases_json = None
        if related_cases:
            # Add timestamp to each related case
            for rc in related_cases:
                rc['detected_at'] = datetime.now().isoformat()
            related_cases_json = json.dumps(related_cases)

        # Create case
        insert_case = """
        INSERT INTO cases (
            case_number, case_title, primary_complaint_id,
            classification, priority,
            complaint_count, auto_grouped, related_cases, status
        ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, 'open')
        RETURNING id
        """

        try:
            with db.get_cursor() as cursor:
                cursor.execute(insert_case, (
                    case_number,
                    case_title,
                    complaint_ids[0],  # Primary complaint
                    primary_classification,
                    primary_priority,
                    len(complaint_ids),
                    auto_grouped,
                    related_cases_json
                ))
                case_id = cursor.fetchone()['id']

            # Add complaints to case
            for i, complaint_id in enumerate(complaint_ids):
                self.add_complaint_to_case(case_id, complaint_id, added_by=added_by)

            print(f"✅ Case {case_number} created with {len(complaint_ids)} complaints")
            return case_id

        except Exception as e:
            print(f"❌ Error creating case: {e}")
            return None

    def add_complaint_to_case(self, case_id: int, complaint_id: int,
                              similarity_score: float = None, added_by: str = 'system'):
        """
        Add complaint to existing case

        Args:
            case_id: Case ID
            complaint_id: Complaint ID
            similarity_score: Optional similarity score
            added_by: 'system' or username
        """
        insert_query = """
        INSERT INTO case_complaints (case_id, complaint_id, similarity_score, added_by)
        VALUES (%s, %s, %s, %s)
        ON CONFLICT (case_id, complaint_id) DO NOTHING
        """

        update_count = """
        UPDATE cases
        SET complaint_count = (
            SELECT COUNT(*) FROM case_complaints WHERE case_id = %s
        ),
        updated_at = CURRENT_TIMESTAMP
        WHERE id = %s
        """

        try:
            with db.get_cursor() as cursor:
                cursor.execute(insert_query, (case_id, complaint_id, similarity_score, added_by))
                cursor.execute(update_count, (case_id, case_id))
            print(f"✅ Complaint {complaint_id} added to case {case_id}")
        except Exception as e:
            print(f"❌ Error adding complaint to case: {e}")

    def remove_complaint_from_case(self, case_id: int, complaint_id: int):
        """Remove complaint from case"""
        delete_query = "DELETE FROM case_complaints WHERE case_id = %s AND complaint_id = %s"
        update_count = """
        UPDATE cases
        SET complaint_count = (
            SELECT COUNT(*) FROM case_complaints WHERE case_id = %s
        ),
        updated_at = CURRENT_TIMESTAMP
        WHERE id = %s
        """

        try:
            with db.get_cursor() as cursor:
                cursor.execute(delete_query, (case_id, complaint_id))
                cursor.execute(update_count, (case_id, case_id))

            # Delete case if no complaints left
            self._delete_empty_cases()
            print(f"✅ Complaint {complaint_id} removed from case {case_id}")
        except Exception as e:
            print(f"❌ Error removing complaint from case: {e}")

    def _delete_empty_cases(self):
        """Delete cases with no complaints"""
        query = "DELETE FROM cases WHERE complaint_count = 0 OR complaint_count IS NULL"
        with db.get_cursor() as cursor:
            cursor.execute(query)

    def find_similar_closed_cases(self, complaint_id: int, top_k: int = 3) -> List[Dict]:
        """
        Find similar cases that are closed (for reference/context)

        Args:
            complaint_id: Complaint ID to search for
            top_k: Number of similar closed cases to return

        Returns:
            List of similar closed cases with similarity scores
        """
        if not self.search_engine:
            return []

        # Get complaint data
        complaint = self.get_complaint_by_id(complaint_id)
        if not complaint:
            return []

        # Prepare search query
        query_text = complaint.get('complaint_description', '')
        if complaint.get('w1h_summary'):
            query_text = f"{query_text} {complaint['w1h_summary']}"

        try:
            # Search for similar complaints
            results = self.search_engine.search(query_text=query_text, top_k=top_k * 3)

            # Filter for complaints in CLOSED cases only
            similar_closed_cases = []
            seen_case_ids = set()

            for result in results:
                result_complaint_id = result.get('id')
                if result_complaint_id == complaint_id:
                    continue

                similarity_score = result.get('similarity_score', 0)
                if similarity_score < self.similarity_threshold:
                    continue

                # Check if this complaint is in a closed case
                case = self.get_case_for_complaint(result_complaint_id)
                if case and case.get('status') == 'closed' and case['id'] not in seen_case_ids:
                    similar_closed_cases.append({
                        'case_id': case['id'],
                        'case_number': case['case_number'],
                        'case_title': case.get('case_title'),
                        'similarity_score': similarity_score,
                        'status': 'closed',
                        'closed_at': case.get('updated_at')
                    })
                    seen_case_ids.add(case['id'])

                if len(similar_closed_cases) >= top_k:
                    break

            return similar_closed_cases

        except Exception as e:
            print(f"❌ Error searching for similar closed cases: {e}")
            return []

    def auto_group_complaint(self, complaint_id: int) -> Optional[int]:
        """
        Auto-group complaint into existing case or create new case.
        Also checks for similar closed cases for reference.

        Args:
            complaint_id: Complaint ID to group

        Returns:
            Case ID (new or existing) or None
        """
        # Check if already in a case
        existing_case = self.get_case_for_complaint(complaint_id)
        if existing_case:
            print(f"ℹ️  Complaint {complaint_id} already in case {existing_case['case_number']}")
            return existing_case['id']

        # Find similar complaints
        similar_complaints = self.find_similar_complaints(complaint_id, top_k=5)

        if not similar_complaints:
            # No similar complaints in open cases
            # Check for similar CLOSED cases (for reference only)
            similar_closed = self.find_similar_closed_cases(complaint_id, top_k=3)

            # Create standalone case with related closed cases reference
            case_id = self.create_case(
                complaint_ids=[complaint_id],
                auto_grouped=False,
                related_cases=similar_closed if similar_closed else None
            )

            if similar_closed:
                print(f"ℹ️  New case created with {len(similar_closed)} related closed case(s) for reference")

            return case_id

        # Check if similar complaints are in existing OPEN cases
        for similar in similar_complaints:
            similar_id = similar.get('id')
            similarity_score = similar.get('similarity_score', 0)

            # High similarity - add to existing case
            if similarity_score >= self.min_similarity_for_auto_group:
                existing_case = self.get_case_for_complaint(similar_id)
                if existing_case and existing_case.get('status') != 'closed':
                    self.add_complaint_to_case(
                        existing_case['id'],
                        complaint_id,
                        similarity_score=similarity_score,
                        added_by='system'
                    )
                    return existing_case['id']

        # No open case found - create new case
        # Check for similar closed cases
        similar_closed = self.find_similar_closed_cases(complaint_id, top_k=3)

        # Create new case with similar complaints
        complaint_ids_to_group = [complaint_id]
        for similar in similar_complaints[:2]:  # Group with top 2 similar
            if similar.get('similarity_score', 0) >= self.min_similarity_for_auto_group:
                similar_id = similar.get('id')
                # Only add if not in another case
                if not self.get_case_for_complaint(similar_id):
                    complaint_ids_to_group.append(similar_id)

        if len(complaint_ids_to_group) > 1:
            case_id = self.create_case(
                complaint_ids=complaint_ids_to_group,
                auto_grouped=True,
                related_cases=similar_closed if similar_closed else None
            )
        else:
            # Create standalone case
            case_id = self.create_case(
                complaint_ids=[complaint_id],
                auto_grouped=False,
                related_cases=similar_closed if similar_closed else None
            )

        if similar_closed:
            print(f"ℹ️  Case created with {len(similar_closed)} related closed case(s) for reference")

        return case_id

    def get_case_details(self, case_id: int) -> Optional[Dict]:
        """
        Get detailed case information including complaints

        Args:
            case_id: Case ID

        Returns:
            Case details with complaints list
        """
        # Get case info
        case_query = "SELECT * FROM cases WHERE id = %s"
        with db.get_cursor() as cursor:
            cursor.execute(case_query, (case_id,))
            case = cursor.fetchone()

        if not case:
            return None

        # Get complaints in case
        complaints_query = """
        SELECT c.*, cc.similarity_score, cc.added_by, cc.added_at
        FROM complaints c
        JOIN case_complaints cc ON c.id = cc.complaint_id
        WHERE cc.case_id = %s
        ORDER BY cc.added_at ASC
        """

        with db.get_cursor() as cursor:
            cursor.execute(complaints_query, (case_id,))
            complaints = cursor.fetchall()

        case['complaints'] = complaints
        return case

    def list_cases(self, status: str = None, limit: int = 50, offset: int = 0) -> List[Dict]:
        """
        List cases with optional filtering

        Args:
            status: Filter by status (open, investigating, closed)
            limit: Number of results
            offset: Pagination offset

        Returns:
            List of cases
        """
        query = "SELECT * FROM cases WHERE 1=1"
        params = []

        if status:
            query += " AND status = %s"
            params.append(status)

        query += " ORDER BY updated_at DESC LIMIT %s OFFSET %s"
        params.extend([limit, offset])

        with db.get_cursor() as cursor:
            cursor.execute(query, tuple(params))
            return cursor.fetchall()

    def update_case(self, case_id: int, updates: Dict) -> bool:
        """
        Update case fields

        Args:
            case_id: Case ID
            updates: Dictionary of fields to update

        Returns:
            True if successful
        """
        allowed_fields = ['case_title', 'case_description', 'status', 'priority', 'classification']

        # Filter allowed fields
        update_fields = {k: v for k, v in updates.items() if k in allowed_fields}

        if not update_fields:
            return False

        # Build UPDATE query
        set_clause = ', '.join([f"{k} = %s" for k in update_fields.keys()])
        query = f"""
        UPDATE cases
        SET {set_clause}, updated_at = CURRENT_TIMESTAMP
        WHERE id = %s
        """

        params = list(update_fields.values()) + [case_id]

        try:
            with db.get_cursor() as cursor:
                cursor.execute(query, tuple(params))
            print(f"✅ Case {case_id} updated")
            return True
        except Exception as e:
            print(f"❌ Error updating case: {e}")
            return False

    def delete_case(self, case_id: int) -> bool:
        """
        Delete a case (also removes case_complaints entries via CASCADE)

        Args:
            case_id: Case ID

        Returns:
            True if successful
        """
        query = "DELETE FROM cases WHERE id = %s"

        try:
            with db.get_cursor() as cursor:
                cursor.execute(query, (case_id,))
            print(f"✅ Case {case_id} deleted")
            return True
        except Exception as e:
            print(f"❌ Error deleting case: {e}")
            return False
