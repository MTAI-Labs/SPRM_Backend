"""
Run complaint fields migration
Makes all complainant fields optional for anonymous complaints
"""
import psycopg2
from dotenv import load_dotenv
import os

load_dotenv()

DB_HOST = os.getenv("DB_HOST", "localhost")
DB_PORT = os.getenv("DB_PORT", "5432")
DB_NAME = os.getenv("DB_NAME", "sprm_db")
DB_USER = os.getenv("DB_USER", "postgres")
DB_PASSWORD = os.getenv("DB_PASSWORD", "postgres")

def run_migration():
    try:
        conn = psycopg2.connect(
            host=DB_HOST,
            port=DB_PORT,
            database=DB_NAME,
            user=DB_USER,
            password=DB_PASSWORD
        )

        print(f"Connected to database: {DB_NAME}")

        with open('update_complaint_fields_migration.sql', 'r', encoding='utf-8') as f:
            migration_sql = f.read()

        cursor = conn.cursor()
        cursor.execute(migration_sql)
        conn.commit()

        print("SUCCESS: Complaint fields updated")
        print("")
        print("Changes:")
        print("  - phone_number: NOW OPTIONAL (was required)")
        print("  - category: REMOVED from submission form")
        print("  - urgency_level: REMOVED from submission form")
        print("")
        print("All complainant information now optional:")
        print("  - full_name (optional)")
        print("  - ic_number (optional)")
        print("  - phone_number (optional)")
        print("  - email (optional)")
        print("")
        print("This allows anonymous complaints!")

        cursor.close()
        conn.close()

    except Exception as e:
        print(f"ERROR: Migration failed - {e}")
        raise

if __name__ == "__main__":
    run_migration()
