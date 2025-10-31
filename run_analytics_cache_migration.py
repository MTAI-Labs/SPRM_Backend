"""
Run analytics cache migration
Creates analytics_cache table for faster dashboard loading
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
    """Run the migration SQL file"""
    try:
        conn = psycopg2.connect(
            host=DB_HOST,
            port=DB_PORT,
            database=DB_NAME,
            user=DB_USER,
            password=DB_PASSWORD
        )

        print(f"Connected to database: {DB_NAME}")

        with open('create_analytics_cache_migration.sql', 'r', encoding='utf-8') as f:
            migration_sql = f.read()

        cursor = conn.cursor()
        cursor.execute(migration_sql)
        conn.commit()

        print("SUCCESS: Analytics cache table created")
        print("")
        print("Table: analytics_cache")
        print("  - cache_key: Unique identifier (e.g., 'dashboard_30d')")
        print("  - cache_data: JSONB with analytics results")
        print("  - created_at: When cache was created")
        print("  - updated_at: When cache was last refreshed")
        print("  - expires_at: Optional expiration time")
        print("")
        print("Benefits:")
        print("  - Dashboard loads instantly (< 100ms)")
        print("  - Auto-refreshed on complaint changes")
        print("  - No redundant processing")

        cursor.close()
        conn.close()

    except Exception as e:
        print(f"ERROR: Migration failed - {e}")
        raise

if __name__ == "__main__":
    run_migration()
