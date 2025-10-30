"""
Classification service - Classify complaints as CRIS or NFA based on 5W1H summary
"""
import os
from typing import Optional, Dict
from openrouter_service import OpenRouterService


class ClassificationService:
    """Service to classify complaints as CRIS (corruption) or NFA (no further action)"""

    def __init__(self, openrouter_service: Optional[OpenRouterService] = None):
        """
        Initialize classification service

        Args:
            openrouter_service: OpenRouter service instance
        """
        self.openrouter = openrouter_service or OpenRouterService()
        # Classification threshold (can be configured)
        self.threshold = float(os.getenv("CLASSIFICATION_THRESHOLD", "0.5"))

    def classify_from_5w1h(self, w1h_summary, complaint_description: str = "") -> Optional[Dict]:
        """
        Classify complaint as CRIS or NFA based on 5W1H summary

        Args:
            w1h_summary: The 5W1H summary (can be string or dict with 'full_text')
            complaint_description: Optional original complaint description

        Returns:
            Dictionary with classification results or None if failed
        """
        # Handle both dict and string formats
        if isinstance(w1h_summary, dict):
            w1h_text = w1h_summary.get('full_text', '')
        else:
            w1h_text = w1h_summary or ''

        if not w1h_text:
            print("⚠️  No 5W1H summary provided for classification")
            return None

        # Build classification prompt
        prompt = self._build_classification_prompt(w1h_text, complaint_description)

        # Call OpenRouter for classification
        result_text = self.openrouter.call_openrouter(
            prompt=prompt,
            max_tokens=500,
            temperature=0.2  # Low temperature for consistent classification
        )

        if not result_text:
            print("❌ Classification failed - no response from AI")
            return None

        # Parse classification result
        classification_result = self._parse_classification(result_text)

        if classification_result:
            print(f"✅ Classification: {classification_result['classification']} "
                  f"(confidence: {classification_result['confidence']:.2%})")

        return classification_result

    def _build_classification_prompt(self, w1h_summary: str, complaint_description: str = "") -> str:
        """Build prompt for classification"""

        prompt = f"""Anda adalah sistem klasifikasi aduan SPRM yang mahir.

Tugas anda adalah untuk mengklasifikasikan aduan sebagai:
- **CRIS** (Case Requiring Investigation - kes yang memerlukan siasatan kerana ada unsur rasuah)
- **NFA** (No Further Action - tiada tindakan lanjut kerana tiada unsur rasuah yang jelas)

Kriteria CRIS (unsur rasuah):
1. Ada pertukaran wang/nilai antara pihak
2. Ada penyalahgunaan kuasa untuk kepentingan peribadi
3. Ada kronisme, nepotisme, atau favoritisme
4. Ada bukti atau petunjuk aktiviti rasuah
5. Melibatkan pegawai awam atau tender kerajaan

Kriteria NFA (bukan rasuah):
1. Aduan tentang perkhidmatan lemah sahaja
2. Tiada pertukaran wang atau nilai
3. Tiada unsur rasuah yang jelas
4. Hanya rungutan umum atau ketidakpuasan hati
5. Di luar bidang kuasa SPRM

RINGKASAN 5W1H:
{w1h_summary}
"""

        if complaint_description:
            prompt += f"\n\nPENERANGAN ASAL ADUAN:\n{complaint_description}\n"

        prompt += """
Analisa dengan teliti dan berikan klasifikasi dalam format JSON:

{
    "classification": "CRIS" atau "NFA",
    "confidence": 0.85,
    "reasoning": "Penjelasan ringkas mengapa diklasifikasikan sebagai CRIS/NFA",
    "corruption_indicators": ["indikator 1", "indikator 2"] atau [],
    "recommendation": "Cadangan tindakan seterusnya"
}

Berikan HANYA JSON (tanpa penjelasan tambahan):"""

        return prompt

    def _parse_classification(self, result_text: str) -> Optional[Dict]:
        """Parse classification result from AI response"""
        import json

        try:
            # Clean the response
            clean_text = result_text.strip()

            # Remove markdown code blocks if present
            if clean_text.startswith('```json'):
                clean_text = clean_text.split('```json')[1].split('```')[0].strip()
            elif clean_text.startswith('```'):
                clean_text = clean_text.split('```')[1].split('```')[0].strip()

            # Parse JSON
            parsed = json.loads(clean_text)

            # Validate required fields
            if 'classification' not in parsed or 'confidence' not in parsed:
                print("⚠️  Invalid classification format - missing required fields")
                return None

            # Normalize classification
            classification = parsed['classification'].upper()
            if classification not in ['CRIS', 'NFA']:
                print(f"⚠️  Invalid classification value: {classification}")
                return None

            # Ensure confidence is between 0 and 1
            confidence = float(parsed['confidence'])
            if confidence > 1:
                confidence = confidence / 100  # Convert percentage to decimal

            # Build result
            result = {
                'classification': classification,
                'confidence': confidence,
                'confidence_percentage': confidence * 100,
                'reasoning': parsed.get('reasoning', ''),
                'corruption_indicators': parsed.get('corruption_indicators', []),
                'recommendation': parsed.get('recommendation', ''),
                'meets_threshold': confidence >= self.threshold
            }

            return result

        except json.JSONDecodeError as e:
            print(f"❌ Failed to parse classification JSON: {e}")
            print(f"   Response was: {result_text[:200]}")
            return None
        except Exception as e:
            print(f"❌ Error parsing classification: {e}")
            return None

    def classify_with_threshold(
        self,
        w1h_summary: str,
        complaint_description: str = "",
        custom_threshold: Optional[float] = None
    ) -> Dict:
        """
        Classify with custom threshold

        Args:
            w1h_summary: 5W1H summary
            complaint_description: Original complaint
            custom_threshold: Custom confidence threshold (0-1)

        Returns:
            Classification result with threshold check
        """
        threshold = custom_threshold if custom_threshold is not None else self.threshold

        result = self.classify_from_5w1h(w1h_summary, complaint_description)

        if not result:
            return {
                'classification': 'UNKNOWN',
                'confidence': 0.0,
                'meets_threshold': False,
                'error': 'Classification failed'
            }

        result['threshold_used'] = threshold
        result['meets_threshold'] = result['confidence'] >= threshold

        return result
