"""
Simple migration script to add summary column
"""
import os
import psycopg2
from psycopg2.extras import RealDictCursor
from dotenv import load_dotenv

# Load environment
load_dotenv()

def run_migration():
    """Add summary column to complaints table"""

    # Database connection parameters
    db_config = {
        'host': os.getenv('DB_HOST', 'localhost'),
        'port': int(os.getenv('DB_PORT', 5432)),
        'database': os.getenv('DB_NAME', 'sprm_db'),
        'user': os.getenv('DB_USER', 'postgres'),
        'password': os.getenv('DB_PASSWORD', 'postgres')
    }

    migration_sql = """
    ALTER TABLE complaints
    ADD COLUMN IF NOT EXISTS summary TEXT;

    COMMENT ON COLUMN complaints.summary IS 'AI-generated executive summary (2-4 sentences) based on complaint form, extracted data, and 5W1H analysis';
    """

    try:
        print("Running migration: Add summary column to complaints table...")

        # Connect to database
        conn = psycopg2.connect(**db_config)
        conn.autocommit = True

        with conn.cursor(cursor_factory=RealDictCursor) as cursor:
            cursor.execute(migration_sql)

        print("SUCCESS: Migration completed!")
        print("- Added 'summary' column to complaints table")

        # Verify the column was added
        with conn.cursor(cursor_factory=RealDictCursor) as cursor:
            cursor.execute("""
                SELECT column_name, data_type
                FROM information_schema.columns
                WHERE table_name = 'complaints' AND column_name = 'summary'
            """)
            result = cursor.fetchone()

            if result:
                print(f"- Column verified: {result['column_name']} ({result['data_type']})")
            else:
                print("WARNING: Could not verify column was added")

        conn.close()
        return True

    except Exception as e:
        print(f"ERROR: Migration failed: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    import sys
    success = run_migration()
    sys.exit(0 if success else 1)
