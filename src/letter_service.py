"""
Letter Generation Service
Generates official letters based on complaint data and templates
"""
from typing import Dict, Optional, List
from datetime import datetime
from database import db
import re


class LetterService:
    """Service for generating official letters from complaint data"""

    def __init__(self, openrouter_service=None):
        """
        Initialize letter service

        Args:
            openrouter_service: Optional OpenRouter service for AI-powered letter generation
        """
        self.openrouter_service = openrouter_service
        # Letter templates will be stored here
        self.templates = {}

    def generate_letter(
        self,
        complaint_id: int,
        letter_type: str,
        additional_data: Optional[Dict] = None
    ) -> Dict:
        """
        Generate a letter based on complaint data

        Args:
            complaint_id: ID of complaint
            letter_type: Type of letter (e.g., 'notification', 'summon', 'closure', 'nfa')
            additional_data: Additional data to include in letter (officer notes, etc.)

        Returns:
            Dict with:
                - letter_content: Generated letter text
                - letter_type: Type of letter
                - generated_at: Timestamp
                - complaint_id: Related complaint ID
        """
        # Get complaint data
        complaint = self._get_complaint_data(complaint_id)
        if not complaint:
            raise ValueError(f"Complaint {complaint_id} not found")

        # Get letter template
        template = self._get_template(letter_type)
        if not template:
            raise ValueError(f"Letter template '{letter_type}' not found")

        # Fill template with data
        letter_content = self._fill_template(
            template=template,
            complaint=complaint,
            additional_data=additional_data or {}
        )

        return {
            'letter_content': letter_content,
            'letter_type': letter_type,
            'generated_at': datetime.now().isoformat(),
            'complaint_id': complaint_id,
            'complaint_reference': f"SPRM/{datetime.now().year}/{complaint_id:05d}"
        }

    def generate_letter_with_ai(
        self,
        complaint_id: int,
        letter_type: str,
        additional_data: Optional[Dict] = None
    ) -> Dict:
        """
        Generate letter using AI (for more complex/custom letters)

        Args:
            complaint_id: ID of complaint
            letter_type: Type of letter
            additional_data: Additional context for AI

        Returns:
            Dict with generated letter
        """
        if not self.openrouter_service:
            raise ValueError("OpenRouter service not available for AI letter generation")

        # Get complaint data
        complaint = self._get_complaint_data(complaint_id)
        if not complaint:
            raise ValueError(f"Complaint {complaint_id} not found")

        # Build prompt for AI
        prompt = self._build_letter_prompt(
            letter_type=letter_type,
            complaint=complaint,
            additional_data=additional_data or {}
        )

        # Generate letter with AI
        letter_content = self.openrouter_service.call_openrouter(
            prompt=prompt,
            max_tokens=1500,
            temperature=0.3  # Lower temperature for formal letters
        )

        return {
            'letter_content': letter_content,
            'letter_type': letter_type,
            'generated_at': datetime.now().isoformat(),
            'complaint_id': complaint_id,
            'complaint_reference': f"SPRM/{datetime.now().year}/{complaint_id:05d}"
        }

    def _get_complaint_data(self, complaint_id: int) -> Optional[Dict]:
        """Get all complaint data needed for letter generation"""
        query = """
        SELECT
            c.*,
            cases.case_number,
            cases.case_title
        FROM complaints c
        LEFT JOIN case_complaints cc ON c.id = cc.complaint_id
        LEFT JOIN cases ON cc.case_id = cases.id
        WHERE c.id = %s
        """

        with db.get_cursor() as cursor:
            cursor.execute(query, (complaint_id,))
            result = cursor.fetchone()
            return dict(result) if result else None

    def _get_template(self, letter_type: str) -> Optional[str]:
        """
        Get letter template by type

        Templates will be defined here or loaded from database/files
        For now, returns placeholder - will be replaced with actual templates
        """
        # Placeholder templates (will be replaced with actual templates from user)
        templates = {
            'notification': """
[TEMPLATE PLACEHOLDER - NOTIFICATION LETTER]
This will be replaced with actual template provided by user.
""",
            'summon': """
[TEMPLATE PLACEHOLDER - SUMMON LETTER]
This will be replaced with actual template provided by user.
""",
            'closure': """
[TEMPLATE PLACEHOLDER - CLOSURE LETTER]
This will be replaced with actual template provided by user.
""",
            'nfa': """
[TEMPLATE PLACEHOLDER - NFA LETTER]
This will be replaced with actual template provided by user.
"""
        }

        return templates.get(letter_type)

    def _fill_template(
        self,
        template: str,
        complaint: Dict,
        additional_data: Dict
    ) -> str:
        """
        Fill template with actual data using placeholder replacement

        Placeholders format: {{field_name}}
        Example: {{complaint_title}}, {{complainant_name}}, {{date}}
        """
        letter = template

        # Current date/time
        now = datetime.now()
        letter = letter.replace('{{current_date}}', now.strftime('%d/%m/%Y'))
        letter = letter.replace('{{current_year}}', str(now.year))
        letter = letter.replace('{{current_time}}', now.strftime('%H:%M'))

        # Complaint reference
        letter = letter.replace('{{complaint_reference}}', f"SPRM/{now.year}/{complaint['id']:05d}")
        letter = letter.replace('{{complaint_id}}', str(complaint['id']))

        # Complainant information
        letter = letter.replace('{{complainant_name}}', complaint.get('full_name') or 'N/A')
        letter = letter.replace('{{complainant_ic}}', complaint.get('ic_number') or 'N/A')
        letter = letter.replace('{{complainant_phone}}', complaint.get('phone_number') or 'N/A')
        letter = letter.replace('{{complainant_email}}', complaint.get('email') or 'N/A')

        # Complaint details
        letter = letter.replace('{{complaint_title}}', complaint.get('complaint_title') or 'N/A')
        letter = letter.replace('{{complaint_category}}', complaint.get('category') or 'N/A')
        letter = letter.replace('{{complaint_description}}', complaint.get('complaint_description') or 'N/A')
        letter = letter.replace('{{submitted_date}}', complaint.get('submitted_at').strftime('%d/%m/%Y') if complaint.get('submitted_at') else 'N/A')

        # Classification & Status
        letter = letter.replace('{{classification}}', complaint.get('classification') or 'N/A')
        letter = letter.replace('{{officer_status}}', complaint.get('officer_status') or 'N/A')

        # Sector information
        letter = letter.replace('{{sector}}', complaint.get('sector') or 'N/A')
        letter = letter.replace('{{sub_sector}}', complaint.get('sub_sector') or 'N/A')

        # Case information
        letter = letter.replace('{{case_number}}', complaint.get('case_number') or 'N/A')

        # Officer remarks
        letter = letter.replace('{{officer_remarks}}', complaint.get('officer_remarks') or 'N/A')

        # Additional data (custom fields from frontend)
        for key, value in additional_data.items():
            placeholder = '{{' + key + '}}'
            letter = letter.replace(placeholder, str(value))

        return letter

    def _build_letter_prompt(
        self,
        letter_type: str,
        complaint: Dict,
        additional_data: Dict
    ) -> str:
        """Build prompt for AI letter generation"""
        prompt = f"""Anda adalah pegawai SPRM yang mahir menulis surat rasmi.

Tugas anda: Tulis surat rasmi jenis '{letter_type}' berdasarkan maklumat aduan berikut.

**Maklumat Aduan:**
- Rujukan: SPRM/{datetime.now().year}/{complaint['id']:05d}
- Tajuk: {complaint.get('complaint_title')}
- Kategori: {complaint.get('category')}
- Sektor: {complaint.get('sector')}
- Sub-Sektor: {complaint.get('sub_sector')}
- Klasifikasi: {complaint.get('classification')}
- Status: {complaint.get('officer_status')}

**Ringkasan 5W1H:**
- Apa: {complaint.get('w1h_what') or 'N/A'}
- Siapa: {complaint.get('w1h_who') or 'N/A'}
- Bila: {complaint.get('w1h_when') or 'N/A'}
- Di mana: {complaint.get('w1h_where') or 'N/A'}
- Mengapa: {complaint.get('w1h_why') or 'N/A'}
- Bagaimana: {complaint.get('w1h_how') or 'N/A'}

**Maklumat Tambahan:**
{additional_data}

Tulis surat yang lengkap dengan format rasmi SPRM, termasuk:
1. Tarikh
2. Rujukan
3. Penerima (jika berkaitan)
4. Tajuk surat
5. Isi kandungan
6. Penutup
7. Tandatangan pegawai

Gunakan Bahasa Malaysia yang formal dan profesional."""

        return prompt

    def get_available_letter_types(self) -> List[Dict]:
        """
        Get list of available letter types

        Returns:
            List of letter types with descriptions
        """
        return [
            {
                'type': 'notification',
                'name': 'Surat Notifikasi',
                'description': 'Surat memberitahu pengadu bahawa aduan telah diterima'
            },
            {
                'type': 'summon',
                'name': 'Surat Panggilan',
                'description': 'Surat memanggil individu untuk memberi keterangan'
            },
            {
                'type': 'closure',
                'name': 'Surat Penutupan Kes',
                'description': 'Surat memberitahu penutupan kes selepas siasatan'
            },
            {
                'type': 'nfa',
                'name': 'Surat NFA (No Further Action)',
                'description': 'Surat memberitahu tiada tindakan lanjut akan diambil'
            },
            {
                'type': 'custom',
                'name': 'Surat Khas (AI)',
                'description': 'Surat khas dijana menggunakan AI berdasarkan konteks'
            }
        ]

    def save_generated_letter(
        self,
        complaint_id: int,
        letter_type: str,
        letter_content: str,
        generated_by: str
    ) -> int:
        """
        Save generated letter to database for record keeping

        Args:
            complaint_id: Related complaint ID
            letter_type: Type of letter
            letter_content: Full letter content
            generated_by: Officer who generated the letter

        Returns:
            Letter ID
        """
        query = """
        INSERT INTO generated_letters (
            complaint_id,
            letter_type,
            letter_content,
            generated_by,
            generated_at
        )
        VALUES (%s, %s, %s, %s, CURRENT_TIMESTAMP)
        RETURNING id
        """

        with db.get_cursor() as cursor:
            cursor.execute(query, (
                complaint_id,
                letter_type,
                letter_content,
                generated_by
            ))
            result = cursor.fetchone()
            return result['id']

    def get_letter_history(self, complaint_id: int) -> List[Dict]:
        """
        Get all letters generated for a complaint

        Args:
            complaint_id: Complaint ID

        Returns:
            List of generated letters
        """
        query = """
        SELECT * FROM generated_letters
        WHERE complaint_id = %s
        ORDER BY generated_at DESC
        """

        with db.get_cursor() as cursor:
            cursor.execute(query, (complaint_id,))
            return cursor.fetchall()
