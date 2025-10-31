"""
Migration script to add related_cases column to cases table
"""
import os
import sys
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent / 'src'))

from database import db


def run_migration():
    """Execute the related cases migration"""

    print("Starting related_cases migration...")

    # Read SQL file
    sql_file = Path(__file__).parent / 'add_related_cases_migration.sql'

    if not sql_file.exists():
        print(f"ERROR: SQL file not found: {sql_file}")
        return False

    with open(sql_file, 'r', encoding='utf-8') as f:
        sql_content = f.read()

    # Execute migration
    try:
        with db.get_cursor() as cursor:
            cursor.execute(sql_content)

        print("SUCCESS: Migration completed successfully!")
        print("   - Added related_cases column to cases table")
        print("   - Created GIN index for JSONB queries")
        return True

    except Exception as e:
        print(f"ERROR: Migration failed: {e}")
        import traceback
        traceback.print_exc()
        return False


if __name__ == "__main__":
    success = run_migration()
    sys.exit(0 if success else 1)
