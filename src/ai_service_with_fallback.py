"""
Enhanced AI Service with Qwen 3 VL 32B primary and OpenRouter fallback
Automatically switches between models based on availability
"""
import os
import requests
from typing import Dict, Optional, List
import json
from pathlib import Path
import base64
import PyPDF2
import time

class AIServiceWithFallback:
    """AI Service that uses Qwen 3 VL 32B as primary with OpenRouter as fallback"""

    def __init__(self):
        """Initialize AI service with both model configurations"""

        # Primary: Qwen 3 VL 32B from boss's server
        self.qwen_base_url = os.getenv("QWEN_BASE_URL", "http://bgpu123.nttdc3.mtailabs.ai:9006/v1")
        self.qwen_model = "Qwen/Qwen3-VL-32B-Instruct"
        self.qwen_available = self._check_qwen_availability()

        # Fallback: OpenRouter
        self.openrouter_api_key = os.getenv("OPENROUTER_API_KEY")
        self.openrouter_base_url = "https://openrouter.ai/api/v1"
        self.openrouter_model = os.getenv("OPENROUTER_MODEL", "qwen/qwen-2.5-vl-72b-instruct")

        # Common settings
        self.timeout = int(os.getenv("AI_TIMEOUT", "120"))
        self.last_availability_check = 0
        self.availability_check_interval = 300  # Re-check every 5 minutes

        # Log initial status
        self._log_status()

    def _log_status(self):
        """Log the current AI service status"""
        print("=" * 60)
        print("🤖 AI Service Status")
        print("=" * 60)
        if self.qwen_available:
            print(f"✅ PRIMARY: Qwen 3 VL 32B at {self.qwen_base_url}")
        else:
            print(f"❌ PRIMARY: Qwen 3 VL 32B unavailable")

        if self.openrouter_api_key:
            print(f"✅ FALLBACK: OpenRouter configured ({self.openrouter_model})")
        else:
            print(f"⚠️  FALLBACK: OpenRouter API key not set")
        print("=" * 60)

    def _check_qwen_availability(self) -> bool:
        """Check if Qwen model server is available"""
        try:
            response = requests.get(
                f"{self.qwen_base_url}/models",
                timeout=5
            )
            if response.status_code == 200:
                models = response.json()
                # Check if our model is in the list
                for model in models.get('data', []):
                    if model.get('id') == self.qwen_model:
                        print(f"✅ Qwen model {self.qwen_model} is available")
                        return True
                print(f"⚠️  Qwen server is up but model {self.qwen_model} not found")
                return False
            return False
        except Exception as e:
            print(f"⚠️  Qwen model server check failed: {e}")
            return False

    def _should_recheck_availability(self) -> bool:
        """Check if we should re-check Qwen availability"""
        current_time = time.time()
        if current_time - self.last_availability_check > self.availability_check_interval:
            return True
        return False

    def _encode_image(self, image_path: str) -> str:
        """Encode image to base64"""
        with open(image_path, "rb") as image_file:
            return base64.b64encode(image_file.read()).decode('utf-8')

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

    def _call_qwen(
        self,
        prompt: str,
        images: Optional[List[str]] = None,
        max_tokens: int = 2000,
        temperature: float = 0.3
    ) -> Optional[str]:
        """Call Qwen 3 VL 32B model"""
        try:
            # Build messages - Qwen uses OpenAI-compatible format
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
                "model": self.qwen_model,
                "messages": [
                    {
                        "role": "user",
                        "content": content
                    }
                ],
                "max_tokens": max_tokens,
                "temperature": temperature
            }

            response = requests.post(
                f"{self.qwen_base_url}/chat/completions",
                json=payload,
                timeout=self.timeout
            )

            if response.status_code == 200:
                result = response.json()
                generated_text = result['choices'][0]['message']['content']
                return generated_text
            else:
                print(f"❌ Qwen request failed: {response.status_code}")
                return None

        except requests.exceptions.Timeout:
            print(f"⏱️  Qwen timeout after {self.timeout}s")
            return None
        except requests.exceptions.ConnectionError:
            print("❌ Qwen connection failed")
            self.qwen_available = False  # Mark as unavailable
            return None
        except Exception as e:
            print(f"❌ Qwen error: {e}")
            return None

    def _call_openrouter(
        self,
        prompt: str,
        images: Optional[List[str]] = None,
        max_tokens: int = 2000,
        temperature: float = 0.3
    ) -> Optional[str]:
        """Call OpenRouter API as fallback"""
        if not self.openrouter_api_key:
            print("❌ OpenRouter API key not configured")
            return None

        try:
            content = [{"type": "text", "text": prompt}]

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
                "model": self.openrouter_model,
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
                "Authorization": f"Bearer {self.openrouter_api_key}",
                "Content-Type": "application/json",
                "HTTP-Referer": "http://localhost:8000",
                "X-Title": "SPRM Complaint System"
            }

            response = requests.post(
                f"{self.openrouter_base_url}/chat/completions",
                headers=headers,
                json=payload,
                timeout=self.timeout
            )

            if response.status_code == 200:
                result = response.json()
                generated_text = result['choices'][0]['message']['content']
                return generated_text
            else:
                print(f"❌ OpenRouter request failed: {response.status_code}")
                if hasattr(response, 'text'):
                    print(f"   Response: {response.text}")
                return None

        except requests.exceptions.Timeout:
            print(f"⏱️  OpenRouter timeout after {self.timeout}s")
            return None
        except Exception as e:
            print(f"❌ OpenRouter error: {e}")
            return None

    def call_ai(
        self,
        prompt: str,
        images: Optional[List[str]] = None,
        max_tokens: int = 2000,
        temperature: float = 0.3,
        prefer_fallback: bool = False
    ) -> Optional[str]:
        """
        Call AI model with automatic fallback

        Args:
            prompt: Text prompt
            images: Optional list of image paths
            max_tokens: Maximum tokens to generate
            temperature: Temperature for generation
            prefer_fallback: Force use of OpenRouter (useful for testing)

        Returns:
            Generated text or None if both models fail
        """

        # Periodically re-check Qwen availability
        if not self.qwen_available and self._should_recheck_availability():
            print("🔄 Re-checking Qwen availability...")
            self.qwen_available = self._check_qwen_availability()
            self.last_availability_check = time.time()

        # Determine which model to use
        if prefer_fallback:
            print("🔄 Using OpenRouter (forced fallback)")
            return self._call_openrouter(prompt, images, max_tokens, temperature)

        # Try primary model first
        if self.qwen_available:
            print("🚀 Using Qwen 3 VL 32B (primary)")
            result = self._call_qwen(prompt, images, max_tokens, temperature)
            if result:
                return result
            print("⚠️  Qwen failed, trying fallback...")

        # Try fallback
        if self.openrouter_api_key:
            print("🔄 Using OpenRouter (fallback)")
            result = self._call_openrouter(prompt, images, max_tokens, temperature)
            if result:
                return result

        print("❌ Both AI models failed")
        return None

    # All the existing methods from OpenRouterService can be added here
    # They would use self.call_ai() instead of self.call_openrouter()

    def _parse_json(self, text: str) -> Dict:
        """Parse JSON from text, handling markdown code blocks"""
        import re

        json_block_pattern = r'```(?:json)?\s*\n?(.*?)\n?```'
        match = re.search(json_block_pattern, text, re.DOTALL)

        if match:
            json_text = match.group(1).strip()
        else:
            json_text = text.strip()

        try:
            return json.loads(json_text)
        except json.JSONDecodeError as e:
            print(f"❌ JSON parse error: {e}")
            print(f"Text: {json_text[:200]}...")
            raise

    def extract_data(self, complaint_text: str) -> Optional[Dict]:
        """Extract structured data from complaint text"""
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

        result = self.call_ai(
            prompt=prompt,
            max_tokens=1000,
            temperature=0.2
        )

        if result:
            try:
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
        """Generate structured 5W1H summary"""

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

        result = self.call_ai(
            prompt=prompt,
            max_tokens=1500,
            temperature=0.3
        )

        if result:
            try:
                w1h_dict = self._parse_json(result)

                full_text = f"""**WHAT (Apa):** {w1h_dict.get('what', 'N/A')}

**WHO (Siapa):** {w1h_dict.get('who', 'N/A')}

**WHEN (Bila):** {w1h_dict.get('when', 'N/A')}

**WHERE (Di mana):** {w1h_dict.get('where', 'N/A')}

**WHY (Mengapa):** {w1h_dict.get('why', 'N/A')}

**HOW (Bagaimana):** {w1h_dict.get('how', 'N/A')}"""

                w1h_dict['full_text'] = full_text
                print(f"✅ 5W1H summary generated")
                return w1h_dict

            except Exception as e:
                print(f"⚠️  Failed to parse 5W1H JSON: {e}")
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

    def get_status(self) -> Dict:
        """Get current service status"""
        return {
            "primary_model": {
                "type": "Qwen 3 VL 32B",
                "url": self.qwen_base_url,
                "available": self.qwen_available,
                "model": self.qwen_model
            },
            "fallback_model": {
                "type": "OpenRouter",
                "configured": bool(self.openrouter_api_key),
                "model": self.openrouter_model
            },
            "last_check": time.strftime("%Y-%m-%d %H:%M:%S", time.localtime(self.last_availability_check))
        }


# Create a singleton instance
_ai_service_instance = None

def get_ai_service() -> AIServiceWithFallback:
    """Get or create the singleton AI service instance"""
    global _ai_service_instance
    if _ai_service_instance is None:
        _ai_service_instance = AIServiceWithFallback()
    return _ai_service_instance