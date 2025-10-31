"""
SPRM Letter Templates
Based on actual SPRM official letter formats (rj-1.pdf, rj-2.pdf)
"""

RUJUK_JABATAN_TEMPLATE = """IBU PEJABAT
SURUHANJAYA PENCEGAHAN RASUAH MALAYSIA
No. 2, Lebuh Wawasan
Presint 7
62250 PUTRAJAYA
Tel: 603-8870 0000
Faks: 603-8870 0901
https://www.sprm.gov.my

Ruj. Tuan     : {{rujukan_tuan}}
Ruj. Kami     : {{rujukan_kami}}
Tarikh        : {{tarikh_surat}}

{{recipient_title}}
{{recipient_name}}
{{recipient_organization}}
{{recipient_address_line1}}
{{recipient_address_line2}}
{{recipient_address_line3}}
{{recipient_state}}

{{salutation}},

{{subject_line}}

Dengan segala hormatnya saya merujuk kepada perkara di atas.

2. Dimaklumkan, Suruhanjaya Pencegahan Rasuah Malaysia (SPRM) telah menerima aduan seperti di atas dan pihak Pengurusan SPRM memutuskan aduan ini sebagai RUJUK JABATAN untuk tindakan lanjut pihak {{recipient_title}}. Sesalinan cabutan aduan adalah seperti di lampiran.

3. Pihak {{recipient_title}} boleh mengemukakan sesalinan hasil tindakan yang telah diambil kepada SPRM melalui alamat e-mel cpm@sprm.gov.my dengan menyatakan nombor rujukan surat ini. Kerjasama dan perhatian pihak {{recipient_title}} berhubung perkara ini amat dihargai. Sebarang pertanyaan, sila hubungi bahagian ini di talian 03-88700635.

Sekian, terima kasih.

"MALAYSIA MADANI"
"BERKHIDMAT UNTUK NEGARA"

Saya yang menjalankan amanah,

{{officer_title}}
{{officer_department}}

b.p Ketua Pesuruhjaya
Suruhanjaya Pencegahan Rasuah
Malaysia

sk. {{cc_line1}}
    {{cc_line2}}

    {{cc_line3}}
    {{cc_line4}}

INI ADALAH JANAAN KOMPUTER, TANDATANGAN TIDAK DIPERLUKAN
"""


# Editable fields configuration for frontend
RUJUK_JABATAN_FIELDS = {
    'auto_filled': {
        'rujukan_tuan': {'label': 'Rujukan Tuan', 'value': '', 'readonly': False},
        'rujukan_kami': {'label': 'Rujukan Kami', 'value': 'SPRM. BPRM. 600-2/3/2 Jld.5({id})', 'readonly': False},
        'tarikh_surat': {'label': 'Tarikh', 'value': '{current_date_malay}', 'readonly': False},
        'subject_line': {'label': 'Tajuk Surat (HURUF BESAR)', 'value': 'ADUAN BERHUBUNG {complaint_title_upper}', 'readonly': False},
    },
    'recipient': {
        'recipient_title': {'label': 'Gelaran Penerima', 'value': 'YBhg. Dato\',', 'options': ['YBhg. Dato\',', 'YBrs. Dato\',', 'Tuan', 'Puan', 'Encik'], 'required': True},
        'recipient_name': {'label': 'Nama Penerima', 'value': '', 'required': True},
        'recipient_organization': {'label': 'Organisasi', 'value': '', 'required': True},
        'recipient_address_line1': {'label': 'Alamat Baris 1', 'value': '', 'required': True},
        'recipient_address_line2': {'label': 'Alamat Baris 2', 'value': '', 'required': False},
        'recipient_address_line3': {'label': 'Alamat Baris 3', 'value': '', 'required': False},
        'recipient_state': {'label': 'Negeri', 'value': '', 'required': True},
        'salutation': {'label': 'Kata Aluan', 'value': 'YBhg. Dato\',', 'options': ['YBhg. Dato\',', 'YBrs. Dato\',', 'Tuan', 'Puan', 'Encik'], 'required': True},
    },
    'officer': {
        'officer_title': {'label': 'Jawatan Pegawai', 'value': 'Pengarah', 'required': True},
        'officer_department': {'label': 'Bahagian', 'value': 'Bahagian Pengurusan Rekod & Maklumat', 'required': True},
    },
    'carbon_copy': {
        'cc_line1': {'label': 'SK Baris 1', 'value': 'Setiausaha Kerajaan', 'required': False},
        'cc_line2': {'label': 'SK Baris 2', 'value': '', 'required': False},
        'cc_line3': {'label': 'SK Baris 3', 'value': '', 'required': False},
        'cc_line4': {'label': 'SK Baris 4', 'value': '', 'required': False},
    }
}


# List of all available templates
AVAILABLE_TEMPLATES = {
    'rujuk_jabatan': {
        'name': 'Surat Rujuk Jabatan',
        'description': 'Surat merujuk aduan kepada jabatan berkaitan untuk tindakan lanjut',
        'template': RUJUK_JABATAN_TEMPLATE,
        'fields': RUJUK_JABATAN_FIELDS
    },
    # Add more templates here
}


def get_template(letter_type: str) -> str:
    """Get template content by type"""
    if letter_type in AVAILABLE_TEMPLATES:
        return AVAILABLE_TEMPLATES[letter_type]['template']
    return None


def get_template_fields(letter_type: str) -> dict:
    """Get editable fields configuration for template"""
    if letter_type in AVAILABLE_TEMPLATES:
        return AVAILABLE_TEMPLATES[letter_type]['fields']
    return {}


def get_available_templates() -> list:
    """Get list of all available templates"""
    return [
        {
            'type': key,
            'name': value['name'],
            'description': value['description']
        }
        for key, value in AVAILABLE_TEMPLATES.items()
    ]
