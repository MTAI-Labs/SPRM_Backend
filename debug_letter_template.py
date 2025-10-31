#!/usr/bin/env python3
"""Debug letter template replacement locally"""

import sys
sys.path.insert(0, 'src')

from letter_templates import get_template

# Get template
template = get_template('rujuk_jabatan')

if not template:
    print("ERROR: Template not found!")
    exit(1)

print("SUCCESS: Template loaded\n")
print("=== ORIGINAL TEMPLATE ===")
print(template)
print("\n" + "="*50 + "\n")

# Simulate field replacement
test_fields = {
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
}

# Replace placeholders (same logic as main.py)
letter_content = template
for key, value in test_fields.items():
    placeholder = '{{' + key + '}}'
    letter_content = letter_content.replace(placeholder, str(value) if value else '')

print("=== GENERATED LETTER ===")
print(letter_content)
print("\n" + "="*50 + "\n")

# Check for unreplaced placeholders
import re
placeholders = re.findall(r'\{\{(\w+)\}\}', letter_content)

if placeholders:
    print("WARNING: Found unreplaced placeholders:")
    for p in set(placeholders):
        print(f"  - {{{{{p}}}}}")
    print(f"\nThese fields are missing from test_fields:")
    for p in set(placeholders):
        if p not in test_fields:
            print(f"  - {p}")
else:
    print("SUCCESS: All placeholders replaced!")

print(f"\nLetter content length: {len(letter_content)} characters")

# Check if "undefined" appears
if 'undefined' in letter_content.lower():
    print("\nERROR: Found 'undefined' in letter content!")
else:
    print("\nSUCCESS: No 'undefined' found in letter content")
