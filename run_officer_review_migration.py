"""
Run officer review migration
Adds officer_status, officer_remarks, reviewed_by, reviewed_at columns
"""
import psycopg2
from dotenv import load_dotenv
import os

load_dotenv()

# Database credentials
DB_HOST = os.getenv("DB_HOST", "localhost")
DB_PORT = os.getenv("DB_PORT", "5432")
DB_NAME = os.getenv("DB_NAME", "sprm_db")
DB_USER = os.getenv("DB_USER", "postgres")
DB_PASSWORD = os.getenv("DB_PASSWORD", "postgres")

def run_migration():
    """Run the migration SQL file"""
    try:
        # Connect to database
        conn = psycopg2.connect(
            host=DB_HOST,
            port=DB_PORT,
            database=DB_NAME,
            user=DB_USER,
            password=DB_PASSWORD
        )

        print(f"Connected to database: {DB_NAME}")

        # Read migration file
        with open('add_officer_review_migration.sql', 'r', encoding='utf-8') as f:
            migration_sql = f.read()

        # Execute migration
        cursor = conn.cursor()
        cursor.execute(migration_sql)
        conn.commit()

        print("SUCCESS: Migration completed successfully")
        print("")
        print("Added columns:")
        print("  - officer_status (VARCHAR)")
        print("  - officer_remarks (TEXT)")
        print("  - reviewed_by (VARCHAR)")
        print("  - reviewed_at (TIMESTAMP)")
        print("")
        print("Officer Status Options:")
        print("  - pending_review: AI processing complete, waiting for officer review")
        print("  - nfa: No Further Action (officer decided not corruption)")
        print("  - escalated: Escalated for investigation")
        print("  - investigating: Under investigation")
        print("  - closed: Case closed")

        cursor.close()
        conn.close()

    except Exception as e:
        print(f"ERROR: Migration failed - {e}")
        raise

if __name__ == "__main__":
    run_migration()
