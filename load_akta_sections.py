"""
Script to load akta sections from list_of_akta.txt into database with embeddings
"""
import sys
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent / 'src'))

from akta_search_service import AktaSearchService


def parse_akta_file(file_path: str) -> list:
    """
    Parse list_of_akta.txt file

    Format: "Seksyen XXX<tab>Description"

    Returns:
        List of tuples (section_code, section_title, category, act_name)
    """
    sections = []

    with open(file_path, 'r', encoding='utf-8') as f:
        for line in f:
            line = line.strip()
            if not line:
                continue

            # Split by tab
            parts = line.split('\t', 1)
            if len(parts) != 2:
                continue

            section_code = parts[0].strip()
            section_title = parts[1].strip()

            # Determine category and act name based on section code
            category = None
            act_name = "Kanun Keseksaan"  # Default

            if "AMLFPUAA" in section_code or "AMLATFPUUA" in section_code:
                category = "Wang Haram"
                act_name = "AMLFPUAA 2001"
            elif any(x in section_title.lower() for x in ['suapan', 'rasuah']):
                category = "Rasuah & Suapan"
            elif any(x in section_title.lower() for x in ['pecah amanah', 'amanah']):
                category = "Pecah Amanah"
            elif any(x in section_title.lower() for x in ['tipu', 'penipuan']):
                category = "Penipuan"
            elif any(x in section_title.lower() for x in ['pals', 'dokumen palsu', 'pemalsuan']):
                category = "Pemalsuan"
            elif any(x in section_title.lower() for x in ['keterangan', 'sijil']):
                category = "Keterangan Palsu"
            elif any(x in section_title.lower() for x in ['pemer', 'paksa']):
                category = "Pemerasan"
            elif any(x in section_title.lower() for x in ['curi', 'salahguna']):
                category = "Curi & Salahguna"
            else:
                category = "Lain-lain"

            sections.append((section_code, section_title, category, act_name))

    return sections


def load_sections_to_db():
    """Load all sections from file to database"""

    print("Starting akta sections loading...")
    print()

    # Initialize service
    service = AktaSearchService()
    service.load_model()

    # Parse file
    akta_file = Path(__file__).parent / 'list_of_akta.txt'
    if not akta_file.exists():
        print(f"ERROR: File not found: {akta_file}")
        return False

    sections = parse_akta_file(akta_file)
    print(f"Found {len(sections)} sections in file")
    print()

    # Load each section
    success_count = 0
    for section_code, section_title, category, act_name in sections:
        print(f"Loading: {section_code} - {section_title[:50]}...")

        success = service.add_section(
            section_code=section_code,
            section_title=section_title,
            description=None,  # No detailed description yet
            category=category,
            act_name=act_name
        )

        if success:
            success_count += 1

    print()
    print(f"SUCCESS: Loaded {success_count}/{len(sections)} sections to database")
    print()

    # Verify
    total = service.count_sections()
    print(f"Total sections in database: {total}")

    return True


if __name__ == "__main__":
    success = load_sections_to_db()
    sys.exit(0 if success else 1)
