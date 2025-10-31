"""
Create simple analytics tables
Pre-computed analytics updated automatically on complaint changes
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

        with open('create_simple_analytics_tables.sql', 'r', encoding='utf-8') as f:
            migration_sql = f.read()

        cursor = conn.cursor()
        cursor.execute(migration_sql)
        conn.commit()

        print("SUCCESS: Simple analytics tables created")
        print("")
        print("Tables Created:")
        print("  1. analytics_entities - Top names, orgs, locations")
        print("  2. analytics_sectors - Sector breakdown")
        print("  3. analytics_patterns - Keyword combinations")
        print("  4. analytics_summary - Overall statistics")
        print("")
        print("How it works:")
        print("  - Complaint processed → Analytics tables updated")
        print("  - Frontend calls API → Read directly from tables")
        print("  - Fast and simple!")

        cursor.close()
        conn.close()

    except Exception as e:
        print(f"ERROR: Migration failed - {e}")
        raise

if __name__ == "__main__":
    run_migration()
