"""
Service for interacting with OpenRouter API (temporary replacement for VLLM)
"""
import os
import requests
from typing import Dict, Optional, List
import json
from pathlib import Path
import base64


class OpenRouterService:
    """Service to interact with OpenRouter API for data extraction and generation"""

    def __init__(self, api_key: Optional[str] = None):
        """
        Initialize OpenRouter service

        Args:
            api_key: OpenRouter API key (default from environment)
        """
        self.api_key = api_key or os.getenv("OPENROUTER_API_KEY")
        self.base_url = "https://openrouter.ai/api/v1"
        self.model = os.getenv("OPENROUTER_MODEL", "qwen/qwen-2.5-vl-72b-instruct")
        self.timeout = int(os.getenv("VLLM_TIMEOUT", "120"))

        if not self.api_key:
            print("⚠️  Warning: OPENROUTER_API_KEY not set")

    def _encode_image(self, image_path: str) -> str:
        """Encode image to base64"""
        with open(image_path, "rb") as image_file:
            return base64.b64encode(image_file.read()).decode('utf-8')

    def _parse_json(self, text: str) -> Dict:
        """
        Parse JSON from text, handling markdown code blocks

        Args:
            text: Text that may contain JSON (possibly in markdown)

        Returns:
            Parsed JSON as dictionary
        """
        import re

        # Strip markdown code blocks if present
        # Pattern: ```json ... ``` or ``` ... ```
        json_block_pattern = r'```(?:json)?\s*\n?(.*?)\n?```'
        match = re.search(json_block_pattern, text, re.DOTALL)

        if match:
            json_text = match.group(1).strip()
        else:
            json_text = text.strip()

        # Try to parse
        try:
            return json.loads(json_text)
        except json.JSONDecodeError as e:
            print(f"❌ JSON parse error: {e}")
            print(f"Text: {json_text[:200]}...")
            raise

    def _get_image_mime_type(self, file_path: str) -> str:
        """Get MIME type for image"""
        ext = Path(file_path).suffix.lower()
        mime_types = {
            '.png': 'image/png',
            '.jpg': 'image/jpeg',
            '.jpeg': 'image/jpeg',
            '.gif': 'image/gif',
            '.webp': 'image/webp'
        }
        return mime_types.get(ext, 'image/jpeg')

    def call_openrouter(
        self,
        prompt: str,
        images: Optional[List[str]] = None,
        max_tokens: int = 2000,
        temperature: float = 0.3
    ) -> Optional[str]:
        """
        Call OpenRouter API with text and optional images

        Args:
            prompt: Text prompt
            images: Optional list of image file paths
            max_tokens: Maximum tokens to generate
            temperature: Temperature for generation

        Returns:
            Generated text or None if failed
        """
        if not self.api_key:
            print("❌ OpenRouter API key not configured")
            return None

        try:
            # Build messages
            content = [{"type": "text", "text": prompt}]

            # Add images if provided
            if images:
                for img_path in images:
                    if Path(img_path).suffix.lower() in ['.png', '.jpg', '.jpeg', '.gif', '.webp']:
                        encoded_image = self._encode_image(img_path)
                        mime_type = self._get_image_mime_type(img_path)
                        content.append({
                            "type": "image_url",
                            "image_url": {
                                "url": f"data:{mime_type};base64,{encoded_image}"
                            }
                        })

            payload = {
                "model": self.model,
                "messages": [
                    {
                        "role": "user",
                        "content": content
                    }
                ],
                "max_tokens": max_tokens,
                "temperature": temperature
            }

            headers = {
                "Authorization": f"Bearer {self.api_key}",
                "Content-Type": "application/json",
                "HTTP-Referer": "http://localhost:8000",  # Optional
                "X-Title": "SPRM Complaint System"  # Optional
            }

            response = requests.post(
                f"{self.base_url}/chat/completions",
                headers=headers,
                json=payload,
                timeout=self.timeout
            )

            response.raise_for_status()
            result = response.json()

            # Extract generated text
            generated_text = result['choices'][0]['message']['content']
            return generated_text

        except requests.exceptions.Timeout:
            print(f"⏱️  OpenRouter API timeout after {self.timeout}s")
            return None
        except requests.exceptions.RequestException as e:
            print(f"❌ OpenRouter API error: {e}")
            if hasattr(e, 'response') and e.response is not None:
                print(f"   Response: {e.response.text}")
            return None
        except Exception as e:
            print(f"❌ Unexpected error: {e}")
            return None

    def extract_from_document(self, file_path: str) -> Optional[Dict]:
        """
        Extract text/data from document using vision model

        Args:
            file_path: Path to the document file

        Returns:
            Dictionary with extracted content
        """
        file_ext = Path(file_path).suffix.lower()

        # For images, use vision model
        if file_ext in ['.png', '.jpg', '.jpeg', '.gif', '.webp']:
            prompt = """Analisa imej ini dengan teliti dan ekstrak semua maklumat penting.

Ekstrak dan kembalikan dalam format JSON:
{
    "text": "semua teks yang kelihatan dalam imej",
    "entities": {
        "names": ["nama-nama yang disebutkan"],
        "locations": ["lokasi-lokasi"],
        "dates": ["tarikh-tarikh"],
        "amounts": ["jumlah wang atau nilai"],
        "organizations": ["organisasi atau syarikat"]
    },
    "description": "penerangan ringkas tentang kandungan imej"
}"""

            result_text = self.call_openrouter(
                prompt=prompt,
                images=[file_path],
                max_tokens=2000,
                temperature=0.2
            )

            if result_text:
                try:
                    # Try to parse as JSON
                    # Remove markdown code blocks if present
                    clean_text = result_text.strip()
                    if clean_text.startswith('```json'):
                        clean_text = clean_text.split('```json')[1].split('```')[0].strip()
                    elif clean_text.startswith('```'):
                        clean_text = clean_text.split('```')[1].split('```')[0].strip()

                    extracted = json.loads(clean_text)
                    print(f"✅ Image extraction completed: {Path(file_path).name}")
                    return extracted
                except json.JSONDecodeError:
                    print(f"⚠️  Could not parse JSON, returning raw text")
                    return {"text": result_text, "raw": True}
            return None

        # For PDFs (can't process directly, return placeholder)
        elif file_ext == '.pdf':
            print(f"⚠️  PDF processing not available in vision model, file: {Path(file_path).name}")
            return {
                "text": f"[PDF file: {Path(file_path).name} - requires OCR processing]",
                "note": "PDF text extraction not available with current setup"
            }

        else:
            print(f"⚠️  Unsupported file type: {file_ext}")
            return None

    def extract_from_multiple_documents(self, file_paths: List[str]) -> List[Dict]:
        """Extract content from multiple documents"""
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

    def extract_data(self, complaint_text: str) -> Optional[Dict]:
        """
        Extract structured data from complaint text

        Args:
            complaint_text: The complaint description

        Returns:
            Dictionary with extracted data
        """
        prompt = f"""Analisa aduan rasuah berikut dan ekstrak maklumat penting dalam format JSON.

ADUAN:
{complaint_text}

Ekstrak dan kembalikan HANYA JSON (tanpa penjelasan tambahan):
{{
    "entities": {{
        "names": ["nama-nama individu atau pegawai yang terlibat"],
        "organizations": ["jabatan, syarikat, atau organisasi yang disebutkan"],
        "locations": ["lokasi atau tempat kejadian"],
        "dates": ["tarikh atau tempoh masa"],
        "amounts": ["jumlah wang atau nilai yang disebutkan"]
    }},
    "summary": "ringkasan 1-2 ayat tentang aduan ini"
}}"""

        result = self.call_openrouter(
            prompt=prompt,
            max_tokens=1000,
            temperature=0.2
        )

        if result:
            try:
                # Clean and parse JSON
                clean_text = result.strip()
                if clean_text.startswith('```json'):
                    clean_text = clean_text.split('```json')[1].split('```')[0].strip()
                elif clean_text.startswith('```'):
                    clean_text = clean_text.split('```')[1].split('```')[0].strip()

                extracted = json.loads(clean_text)
                print(f"✅ Data extraction completed")
                return extracted
            except json.JSONDecodeError:
                print(f"⚠️  Could not parse extraction result as JSON")
                return {"raw_text": result}

        return None

    def generate_5w1h(self, complaint_text: str, extracted_data: Optional[Dict] = None) -> Optional[Dict]:
        """
        Generate structured 5W1H summary

        Returns:
            Dictionary with keys: what, who, when, where, why, how, full_text
        """

        context = complaint_text
        if extracted_data:
            context += f"\n\nMaklumat yang diekstrak:\n{json.dumps(extracted_data, indent=2, ensure_ascii=False)}"

        prompt = f"""Anda adalah pembantu AI yang mahir dalam menganalisis aduan rasuah.

Berdasarkan maklumat aduan di bawah, hasilkan ringkasan 5W1H yang jelas dan terperinci dalam format JSON.

ADUAN:
{context}

Hasilkan ringkasan 5W1H dalam format JSON berikut (gunakan Bahasa Malaysia):

{{
  "what": "Perkara/isu utama yang dilaporkan dengan jelas",
  "who": "Individu/pihak yang terlibat - nama, jawatan jika ada",
  "when": "Masa/tempoh kejadian berlaku",
  "where": "Lokasi kejadian dengan spesifik",
  "why": "Sebab/motif kejadian atau tujuan aduan",
  "how": "Cara/kaedah bagaimana kejadian berlaku"
}}

Pastikan setiap field dijawab dengan lengkap berdasarkan maklumat yang ada.
Jika maklumat tidak mencukupi, tulis "Tidak dinyatakan" atau "Maklumat tidak lengkap".

JSON sahaja, tanpa penjelasan tambahan:"""

        result = self.call_openrouter(
            prompt=prompt,
            max_tokens=1500,
            temperature=0.3
        )

        if result:
            # Parse JSON response
            try:
                w1h_dict = self._parse_json(result)

                # Create full text version for backward compatibility
                full_text = f"""**WHAT (Apa):** {w1h_dict.get('what', 'N/A')}

**WHO (Siapa):** {w1h_dict.get('who', 'N/A')}

**WHEN (Bila):** {w1h_dict.get('when', 'N/A')}

**WHERE (Di mana):** {w1h_dict.get('where', 'N/A')}

**WHY (Mengapa):** {w1h_dict.get('why', 'N/A')}

**HOW (Bagaimana):** {w1h_dict.get('how', 'N/A')}"""

                w1h_dict['full_text'] = full_text

                print(f"✅ 5W1H summary generated (structured)")
                return w1h_dict

            except Exception as e:
                print(f"⚠️  Failed to parse 5W1H JSON: {e}")
                print(f"Raw response: {result[:200]}...")

                # Fallback: return as full_text only
                return {
                    'what': None,
                    'who': None,
                    'when': None,
                    'where': None,
                    'why': None,
                    'how': None,
                    'full_text': result
                }

        return None

    def generate_sector(self, w1h_summary: Dict, complaint_text: str) -> Optional[str]:
        """
        Determine the government sector this complaint falls under

        Args:
            w1h_summary: The structured 5W1H data
            complaint_text: Original complaint description

        Returns:
            Sector name as string
        """
        # Get full text for analysis
        if isinstance(w1h_summary, dict):
            w1h_text = w1h_summary.get('full_text', '')
        else:
            w1h_text = w1h_summary or ''

        prompt = f"""Berdasarkan aduan berikut, tentukan SATU sektor kerajaan yang paling berkaitan.

**Ringkasan 5W1H:**
{w1h_text}

**Deskripsi Asal:**
{complaint_text[:500]}

**Pilih dari 10 sektor berikut:**
1. Pendidikan (Education) - Sekolah, universiti, pelajar, guru, pendaftaran
2. Kesihatan (Health) - Hospital, klinik, ubat-ubatan, perkhidmatan kesihatan
3. Pengangkutan (Transportation) - Jalan raya, pengangkutan awam, lesen memandu, JPJ
4. Pembinaan & Infrastruktur (Construction & Infrastructure) - Kontrak pembinaan, projek kerajaan, JKR
5. Perkhidmatan Awam (Public Service) - Pegawai kerajaan, birokrasi, perkhidmatan pentadbiran
6. Kewangan & Cukai (Finance & Tax) - LHDN, kastam, tender, subsidi, peruntukan
7. Polis & Keselamatan (Police & Security) - PDRM, imigresen, penguatkuasaan undang-undang
8. Tanah & Perumahan (Land & Housing) - Tanah kerajaan, perumahan awam, pejabat tanah
9. Alam Sekitar (Environment) - Kebersihan, sampah, hutan, air, pencemaran
10. Lain-lain (Others) - Sektor yang tidak sesuai dengan kategori di atas

Jawab dengan NAMA SEKTOR sahaja (contoh: "Pendidikan" atau "Kewangan & Cukai"). Jangan beri penjelasan tambahan."""

        result = self.call_openrouter(prompt=prompt, max_tokens=100, temperature=0.2)

        if result:
            sector = result.strip()
            print(f"✅ Sector determined: {sector}")
            return sector

        return None

    def generate_akta(self, w1h_summary: Dict, complaint_text: str, sector: Optional[str] = None) -> Optional[str]:
        """
        Determine the relevant Malaysian legislation (Akta) for this complaint

        Args:
            w1h_summary: The structured 5W1H data
            complaint_text: Original complaint description
            sector: The determined sector (optional, helps with context)

        Returns:
            Akta name as string
        """
        # Get full text for analysis
        if isinstance(w1h_summary, dict):
            w1h_text = w1h_summary.get('full_text', '')
        else:
            w1h_text = w1h_summary or ''

        sector_context = f"\n**Sektor:** {sector}" if sector else ""

        prompt = f"""Berdasarkan aduan rasuah/salah laku berikut, tentukan SATU akta Malaysia yang paling berkaitan.

**Ringkasan 5W1H:**
{w1h_text}{sector_context}

**Deskripsi Asal:**
{complaint_text[:500]}

**Pilih dari 10 akta berikut:**
1. Akta Suruhanjaya Pencegahan Rasuah Malaysia 2009 (SPRM Act) - Rasuah, suapan, salah guna kuasa
2. Akta Keterangan 1950 (Evidence Act) - Bukti, prosedur keterangan
3. Akta Kesalahan Keselamatan (Langkah-Langkah Khas) 2012 (SOSMA) - Ancaman keselamatan, jenayah terancang
4. Akta Pencegahan Pengubahan Wang Haram, Pencegahan Pembiayaan Keganasan dan Hasil Daripada Aktiviti Haram 2001 (AMLATFPUUA) - Wang haram, pembiayaan keganasan
5. Akta Kontrak Kerajaan 1949 (Government Contracts Act) - Kontrak dengan kerajaan, tender
6. Akta Tatacara Kewangan 1957 (Financial Procedure Act) - Pengurusan kewangan kerajaan
7. Akta Perintah Am (Revised 1980) (General Orders) - Peraturan perkhidmatan awam
8. Akta Tatacara Jenayah 1999 (Criminal Procedure Code) - Prosedur jenayah, tangkapan, siasatan
9. Akta Kanun Keseksaan (Penal Code) - Jenayah am, penipuan, pecah amanah
10. Akta-akta Lain (Other Acts) - Tidak sesuai dengan kategori di atas

Jawab dengan NAMA AKTA sahaja (contoh: "Akta SPRM 2009" atau "Akta Kanun Keseksaan"). Jangan beri penjelasan tambahan."""

        result = self.call_openrouter(prompt=prompt, max_tokens=150, temperature=0.2)

        if result:
            akta = result.strip()
            print(f"✅ Akta determined: {akta}")
            return akta

        return None

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
            print(f"📄 Processing {len(document_paths)} document(s) with OpenRouter vision model...")
            doc_extractions = self.extract_from_multiple_documents(document_paths)
            results["document_extractions"] = doc_extractions

            # Combine extracted text from documents
            for doc_result in doc_extractions:
                if doc_result.get('extracted_content'):
                    extracted_content = doc_result['extracted_content']

                    # Get text from extraction
                    doc_text = extracted_content.get('text', '')
                    doc_desc = extracted_content.get('description', '')

                    combined_doc_text = f"{doc_text}\n{doc_desc}".strip()

                    if combined_doc_text:
                        all_extracted_text += f"\n\n--- Maklumat dari {doc_result['filename']} ---\n{combined_doc_text}"

        # Step 2: Extract structured data from combined text
        print("🔍 Extracting structured data...")
        extracted_data = self.extract_data(all_extracted_text)
        if extracted_data:
            results["extracted_data"] = extracted_data

        # Step 3: Generate 5W1H from everything
        print("📝 Generating 5W1H summary...")
        w1h_summary = self.generate_5w1h(all_extracted_text, extracted_data)
        if w1h_summary:
            results["w1h_summary"] = w1h_summary

        # Mark as successful if at least one step worked
        results["success"] = bool(extracted_data or w1h_summary or results["document_extractions"])

        return results

    def generate_complaint_summary(
        self,
        complaint_data: Dict,
        extracted_data: Optional[Dict] = None,
        w1h_summary: Optional[Dict] = None
    ) -> Optional[str]:
        """
        Generate a comprehensive summary of the complaint based on all available data

        Args:
            complaint_data: Original complaint form data (title, description, etc.)
            extracted_data: Extracted entities and information
            w1h_summary: 5W1H structured analysis

        Returns:
            A concise summary paragraph (2-4 sentences) in Bahasa Malaysia
        """
        # Build context from all available data
        context_parts = []

        # Add original complaint
        context_parts.append(f"**Tajuk Aduan:** {complaint_data.get('complaint_title', 'N/A')}")
        context_parts.append(f"**Deskripsi:** {complaint_data.get('complaint_description', 'N/A')}")
        context_parts.append(f"**Kategori:** {complaint_data.get('category', 'N/A')}")
        context_parts.append(f"**Tahap Kecemasan:** {complaint_data.get('urgency_level', 'N/A')}")

        # Add extracted data if available
        if extracted_data:
            context_parts.append(f"\n**Data Yang Diekstrak:**")
            if extracted_data.get('entities'):
                entities = extracted_data['entities']
                if entities.get('names'):
                    context_parts.append(f"- Nama: {', '.join(entities['names'])}")
                if entities.get('organizations'):
                    context_parts.append(f"- Organisasi: {', '.join(entities['organizations'])}")
                if entities.get('locations'):
                    context_parts.append(f"- Lokasi: {', '.join(entities['locations'])}")
                if entities.get('amounts'):
                    context_parts.append(f"- Jumlah: {', '.join(entities['amounts'])}")

        # Add 5W1H if available
        if w1h_summary:
            if isinstance(w1h_summary, dict):
                context_parts.append(f"\n**Analisis 5W1H:**")
                context_parts.append(f"- Apa: {w1h_summary.get('what', 'N/A')}")
                context_parts.append(f"- Siapa: {w1h_summary.get('who', 'N/A')}")
                context_parts.append(f"- Bila: {w1h_summary.get('when', 'N/A')}")
                context_parts.append(f"- Di mana: {w1h_summary.get('where', 'N/A')}")
                context_parts.append(f"- Mengapa: {w1h_summary.get('why', 'N/A')}")
                context_parts.append(f"- Bagaimana: {w1h_summary.get('how', 'N/A')}")
            else:
                context_parts.append(f"\n**Ringkasan 5W1H:** {w1h_summary}")

        context = "\n".join(context_parts)

        prompt = f"""Anda adalah penolong analis SPRM yang mahir. Berdasarkan semua maklumat aduan di bawah, hasilkan RINGKASAN EKSEKUTIF yang ringkas dan padat.

{context}

**Tugasan:**
Hasilkan ringkasan eksekutif dalam 2-4 ayat yang merangkumi:
1. Inti pati aduan (apa yang dilaporkan)
2. Pihak yang terlibat (siapa)
3. Lokasi dan masa (jika ada)
4. Implikasi atau tindakan yang diperlukan

**Format:**
- Gunakan Bahasa Malaysia yang formal dan profesional
- Ringkas tetapi lengkap (2-4 ayat sahaja)
- Fokus kepada fakta utama
- Tiada bullet points, hanya perenggan

Ringkasan eksekutif sahaja, tanpa tajuk atau pengenalan:"""

        result = self.call_openrouter(
            prompt=prompt,
            max_tokens=500,
            temperature=0.3
        )

        if result:
            summary = result.strip()
            # Remove any markdown formatting
            summary = summary.replace('**', '').replace('*', '')
            print(f"✅ Complaint summary generated ({len(summary)} chars)")
            return summary

        return None
