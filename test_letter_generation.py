#!/usr/bin/env python3
"""Test letter generation to see what's being returned"""

import requests
import json

# Test data
test_data = {
    "letter_type": "rujuk_jabatan",
    "fields": {
        "rujukan_tuan": "",
        "rujukan_kami": "SPRM. BPRM. 600-2/3/2 Jld.5(45)",
        "tarikh_surat": "31 Oktober 2025",
        "recipient_title": "YBhg. Dato',",
        "recipient_name": "Datuk Bandar",
        "recipient_organization": "Majlis Bandaraya Johor Bahru",
        "recipient_address_line1": "Menara MBJB, No. 1",
        "recipient_address_line2": "Jalan Lingkaran Dalam",
        "recipient_address_line3": "Bukit Senyum, 80300 Johor Bahru",
        "recipient_state": "JOHOR",
        "salutation": "YBhg. Dato',",
        "subject_line": "ADUAN BERHUBUNG RASUAH",
        "officer_title": "Pengarah",
        "officer_department": "Bahagian Pengurusan Rekod & Maklumat",
        "cc_line1": "Setiausaha Kerajaan Negeri Johor",
        "cc_line2": "",
        "cc_line3": "",
        "cc_line4": ""
    },
    "generated_by": "test_officer"
}

# Make request
response = requests.post(
    'http://localhost:8000/complaints/45/letters/generate',
    json=test_data
)

print(f"Status Code: {response.status_code}")
print(f"\nResponse JSON:")
result = response.json()
print(json.dumps(result, indent=2))

print(f"\n\n=== LETTER CONTENT ===")
if 'letter_content' in result:
    print(result['letter_content'])

    # Check for unreplaced placeholders
    if '{{' in result['letter_content']:
        print("\n\n⚠️  WARNING: Found unreplaced placeholders:")
        import re
        placeholders = re.findall(r'\{\{(\w+)\}\}', result['letter_content'])
        for p in set(placeholders):
            print(f"  - {{{{{p}}}}}")
else:
    print("❌ letter_content is MISSING from response!")
    print("Available keys:", list(result.keys()))
