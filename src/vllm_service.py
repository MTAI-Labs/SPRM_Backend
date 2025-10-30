"""
Service for interacting with external VLLM API
"""
import os
import requests
from typing import Dict, Optional, List
import json
from pathlib import Path


class VLLMService:
    """Service to interact with VLLM API for data extraction and generation"""

    def __init__(self, base_url: Optional[str] = None):
        """
        Initialize VLLM service

        Args:
            base_url: Base URL of VLLM API (default from environment)
        """
        self.base_url = base_url or os.getenv("VLLM_API_URL", "http://localhost:8000")
        self.timeout = int(os.getenv("VLLM_TIMEOUT", "120"))  # 120 seconds for document processing

    def extract_data(self, complaint_text: str) -> Optional[Dict]:
        """
        Call VLLM API to extract structured data from complaint text

        Args:
            complaint_text: The complaint description

        Returns:
            Dictionary with extracted data or None if failed
        """
        try:
            # Prepare request payload
            # Adjust this based on your VLLM API's expected format
            payload = {
                "text": complaint_text,
                "task": "extract"
            }

            # Call VLLM API
            response = requests.post(
                f"{self.base_url}/extract",
                json=payload,
                timeout=self.timeout
            )

            response.raise_for_status()
            result = response.json()

            print(f"✅ Data extraction completed via VLLM API")
            return result

        except requests.exceptions.Timeout:
            print(f"⏱️  VLLM API timeout after {self.timeout}s")
            return None
        except requests.exceptions.ConnectionError:
            print(f"❌ Cannot connect to VLLM API at {self.base_url}")
            return None
        except Exception as e:
            print(f"❌ VLLM extraction error: {e}")
            return None

    def generate_5w1h(self, complaint_text: str, extracted_data: Optional[Dict] = None) -> Optional[str]:
        """
        Generate 5W1H summary from complaint text and extracted data

        Args:
            complaint_text: Original complaint description
            extracted_data: Optional extracted data from previous step

        Returns:
            5W1H summary string or None if failed
        """
        try:
            # Build context for 5W1H generation
            context = complaint_text

            if extracted_data:
                # Include extracted data in context
                context += f"\n\nExtracted Information:\n{json.dumps(extracted_data, indent=2)}"

            # Prompt for 5W1H generation
            prompt = self._build_5w1h_prompt(context)

            # Call VLLM API for generation
            payload = {
                "prompt": prompt,
                "max_tokens": 500,
                "temperature": 0.3,
                "task": "generate"
            }

            response = requests.post(
                f"{self.base_url}/generate",
                json=payload,
                timeout=self.timeout
            )

            response.raise_for_status()
            result = response.json()

            # Extract generated text (adjust based on your API response format)
            generated_text = result.get("generated_text") or result.get("text") or result.get("response")

            if generated_text:
                print(f"✅ 5W1H generation completed via VLLM API")
                return generated_text
            else:
                print(f"⚠️  VLLM API returned empty response")
                return None

        except requests.exceptions.Timeout:
            print(f"⏱️  VLLM API timeout after {self.timeout}s")
            return None
        except requests.exceptions.ConnectionError:
            print(f"❌ Cannot connect to VLLM API at {self.base_url}")
            return None
        except Exception as e:
            print(f"❌ VLLM 5W1H generation error: {e}")
            return None

    def _build_5w1h_prompt(self, complaint_text: str) -> str:
        """
        Build prompt for 5W1H generation

        Args:
            complaint_text: The complaint text with optional extracted data

        Returns:
            Formatted prompt string
        """
        prompt = f"""Anda adalah pembantu AI yang mahir dalam menganalisis aduan rasuah.

Berdasarkan maklumat aduan di bawah, hasilkan ringkasan 5W1H (What, Who, When, Where, Why, How) dalam format yang jelas dan terstruktur.

ADUAN:
{complaint_text}

Hasilkan ringkasan 5W1H dalam format berikut:

**WHAT (Apa):** [Perkara/isu utama yang dilaporkan]

**WHO (Siapa):** [Individu/pihak yang terlibat]

**WHEN (Bila):** [Masa/tempoh kejadian]

**WHERE (Di mana):** [Lokasi kejadian]

**WHY (Mengapa):** [Sebab/motif kejadian]

**HOW (Bagaimana):** [Cara/kaedah kejadian berlaku]

Ringkasan 5W1H:"""

        return prompt

    def generate_5w1h_structured(self, complaint_text: str, extracted_data: Optional[Dict] = None) -> Optional[Dict]:
        """
        Generate 5W1H summary in structured JSON format

        Args:
            complaint_text: Original complaint description
            extracted_data: Optional extracted data from previous step

        Returns:
            Dictionary with 5W1H fields or None if failed
        """
        try:
            # Build context
            context = complaint_text
            if extracted_data:
                context += f"\n\nExtracted Information:\n{json.dumps(extracted_data, indent=2)}"

            # Prompt for structured 5W1H
            prompt = f"""Analyze the following complaint and extract 5W1H information in JSON format.

COMPLAINT:
{context}

Return a JSON object with the following structure:
{{
    "what": "Description of what happened",
    "who": "People/entities involved",
    "when": "Time/date of incident",
    "where": "Location of incident",
    "why": "Reason/motive",
    "how": "Method/manner of occurrence"
}}

JSON Response:"""

            payload = {
                "prompt": prompt,
                "max_tokens": 400,
                "temperature": 0.2,
                "task": "generate_json"
            }

            response = requests.post(
                f"{self.base_url}/generate",
                json=payload,
                timeout=self.timeout
            )

            response.raise_for_status()
            result = response.json()

            # Try to parse JSON from response
            generated_text = result.get("generated_text") or result.get("text") or result.get("response")

            if generated_text:
                # Try to parse as JSON
                try:
                    parsed = json.loads(generated_text)
                    print(f"✅ Structured 5W1H generation completed")
                    return parsed
                except json.JSONDecodeError:
                    print(f"⚠️  Could not parse 5W1H as JSON, returning as text")
                    return {"raw_text": generated_text}
            else:
                return None

        except Exception as e:
            print(f"❌ VLLM structured 5W1H error: {e}")
            return None

    def extract_from_document(self, file_path: str) -> Optional[Dict]:
        """
        Send document to VLLM API for content extraction

        Args:
            file_path: Path to the document file

        Returns:
            Dictionary with extracted content or None if failed
        """
        try:
            # Open file and send to VLLM
            with open(file_path, 'rb') as f:
                files = {
                    'file': (Path(file_path).name, f, self._get_content_type(file_path))
                }

                # You can also send additional parameters
                data = {
                    'task': 'extract_document'
                }

                response = requests.post(
                    f"{self.base_url}/extract/document",
                    files=files,
                    data=data,
                    timeout=self.timeout
                )

                response.raise_for_status()
                result = response.json()

                print(f"✅ Document extraction completed: {Path(file_path).name}")
                return result

        except requests.exceptions.Timeout:
            print(f"⏱️  Document extraction timeout for {Path(file_path).name}")
            return None
        except requests.exceptions.ConnectionError:
            print(f"❌ Cannot connect to VLLM API for document extraction")
            return None
        except Exception as e:
            print(f"❌ Document extraction error for {Path(file_path).name}: {e}")
            return None

    def extract_from_multiple_documents(self, file_paths: List[str]) -> List[Dict]:
        """
        Extract content from multiple documents

        Args:
            file_paths: List of file paths

        Returns:
            List of extraction results
        """
        results = []

        for file_path in file_paths:
            print(f"📄 Processing document: {Path(file_path).name}")
            extraction = self.extract_from_document(file_path)

            if extraction:
                results.append({
                    'filename': Path(file_path).name,
                    'file_path': file_path,
                    'extracted_content': extraction
                })
            else:
                results.append({
                    'filename': Path(file_path).name,
                    'file_path': file_path,
                    'extracted_content': None,
                    'error': 'Extraction failed'
                })

        return results

    def _get_content_type(self, file_path: str) -> str:
        """Get content type based on file extension"""
        ext = Path(file_path).suffix.lower()
        content_types = {
            '.pdf': 'application/pdf',
            '.png': 'image/png',
            '.jpg': 'image/jpeg',
            '.jpeg': 'image/jpeg',
            '.txt': 'text/plain',
            '.doc': 'application/msword',
            '.docx': 'application/vnd.openxmlformats-officedocument.wordprocessingml.document'
        }
        return content_types.get(ext, 'application/octet-stream')

    def process_complaint_with_vllm(
        self,
        complaint_text: str,
        document_paths: Optional[List[str]] = None
    ) -> Dict:
        """
        Complete processing pipeline: extract from documents + form data + generate 5W1H

        Args:
            complaint_text: The complaint description from form
            document_paths: Optional list of uploaded document file paths

        Returns:
            Dictionary with extracted_data, document_extractions, and w1h_summary
        """
        results = {
            "extracted_data": None,
            "document_extractions": [],
            "w1h_summary": None,
            "success": False
        }

        # Step 1: Extract from documents (if any)
        all_extracted_text = complaint_text
        if document_paths:
            print(f"📄 Processing {len(document_paths)} document(s)...")
            doc_extractions = self.extract_from_multiple_documents(document_paths)
            results["document_extractions"] = doc_extractions

            # Combine extracted text from documents
            for doc_result in doc_extractions:
                if doc_result.get('extracted_content'):
                    extracted_content = doc_result['extracted_content']

                    # Assuming VLLM returns text in a 'text' or 'content' field
                    doc_text = extracted_content.get('text') or extracted_content.get('content') or str(extracted_content)
                    all_extracted_text += f"\n\n--- From {doc_result['filename']} ---\n{doc_text}"

        # Step 2: Extract structured data from combined text
        extracted_data = self.extract_data(all_extracted_text)
        if extracted_data:
            results["extracted_data"] = extracted_data

        # Step 3: Generate 5W1H from everything
        w1h_summary = self.generate_5w1h(all_extracted_text, extracted_data)
        if w1h_summary:
            results["w1h_summary"] = w1h_summary

        # Mark as successful if at least one step worked
        results["success"] = bool(extracted_data or w1h_summary or results["document_extractions"])

        return results
