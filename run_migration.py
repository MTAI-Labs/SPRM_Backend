"""
Run database migration to add summary column
"""
import os
import sys
from dotenv import load_dotenv

# Add src to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

# Load environment
load_dotenv()

from database import db

def run_migration():
    """Add summary column to complaints table"""

    migration_sql = """
    -- Add summary column to complaints table
    ALTER TABLE complaints
    ADD COLUMN IF NOT EXISTS summary TEXT;

    COMMENT ON COLUMN complaints.summary IS 'AI-generated executive summary (2-4 sentences) based on complaint form, extracted data, and 5W1H analysis';
    """

    try:
        print("🔄 Running migration: Add summary column to complaints table...")

        with db.get_cursor() as cursor:
            cursor.execute(migration_sql)

        print("✅ Migration completed successfully!")
        print("   - Added 'summary' column to complaints table")

        # Verify the column was added
        with db.get_cursor() as cursor:
            cursor.execute("""
                SELECT column_name, data_type
                FROM information_schema.columns
                WHERE table_name = 'complaints' AND column_name = 'summary'
            """)
            result = cursor.fetchone()

            if result:
                print(f"   - Column verified: {result['column_name']} ({result['data_type']})")
            else:
                print("   ⚠️  Warning: Could not verify column was added")

        return True

    except Exception as e:
        print(f"❌ Migration failed: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    success = run_migration()
    sys.exit(0 if success else 1)
