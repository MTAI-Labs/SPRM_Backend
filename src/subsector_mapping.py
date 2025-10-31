"""
Sector and Sub-Sector Mapping Configuration
Based on list_of_sectors.txt
"""

# Main sectors (bilingual format)
MAIN_SECTORS = [
    "Business and Industry / Perniagaan dan Industri",
    "Financing and Revenue / Pembiayaan dan Pendapatan",
    "Defence and Security / Pertahanan dan Keselamatan",
    "Investment / Pelaburan",
    "Services / Perkhidmatan",
    "Legal Affairs and Judiciary / Hal Ehwal Perundangan dan Kehakiman",
    "Licencing and Permit / Perlesenan dan Permit",
    "Procurement / Perolehan",
    "Enforcement / Penguatkuasaan",
    "Administration / Pentadbiran"
]

# Sub-sectors (apply to all main sectors)
# Officers can select any sub-sector regardless of main sector
SUB_SECTORS = [
    "Perundangan Sistem Prosedur dan Peraturan",
    "Umum / Pelbagai",
    "Perundingan",
    "Perkhidmatan",
    "Kerja dan Gred",
    "Bekalan",
    "Pelacuran / Rumah Urut",
    "Penyeludupan / Barang Keluar Masuk",
    "Aktiviti Jenayah Umum",
    "Penguatkuasaan Lesen",
    "Perjudian / Kongsi Gelap",
    "Dadah / Narkotik",
    "Jalanraya / Kenderaan",
    "Pati / Pencerobohan",
    "Perburuan",
    "Persenjataan",
    "Perlombongan",
    "Pembalakan",
    "Pengangkutan",
    "Tanah",
    "Perniagaan"
]

# Type of Information options (can be edited when actual data provided)
TYPE_OF_INFORMATION_OPTIONS = [
    "Intelligence",
    "Complaint",
    "Report",
    "Whistleblower",
    "Anonymous Tip",
    "Media Report",
    "Others"
]

# Source Type options (can be edited when actual data provided)
SOURCE_TYPE_OPTIONS = [
    "Public / Walk-in",
    "Government Agency",
    "Media",
    "Online Portal",
    "Hotline / Phone",
    "Letter / Mail",
    "Social Media",
    "Others"
]

# Currency types for CRIS details
CURRENCY_TYPES = [
    "MYR",
    "USD",
    "SGD",
    "EUR",
    "GBP",
    "CNY",
    "Others"
]


def get_main_sectors():
    """Get list of main sectors"""
    return MAIN_SECTORS


def get_sub_sectors():
    """Get list of sub-sectors (applicable to all main sectors)"""
    return SUB_SECTORS


def get_type_of_information_options():
    """Get type of information options"""
    return TYPE_OF_INFORMATION_OPTIONS


def get_source_type_options():
    """Get source type options"""
    return SOURCE_TYPE_OPTIONS


def get_currency_types():
    """Get currency type options"""
    return CURRENCY_TYPES


# Note: To update these options in the future:
# 1. Edit the lists above in this file
# 2. Restart the backend server
# 3. Frontend will fetch updated options from /config/evaluation-options endpoint
