"""
Run letters table migration
Creates table for storing generated letters
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

        with open('create_letters_table_migration.sql', 'r', encoding='utf-8') as f:
            migration_sql = f.read()

        cursor = conn.cursor()
        cursor.execute(migration_sql)
        conn.commit()

        print("SUCCESS: Letters table created")
        print("")
        print("Table: generated_letters")
        print("  - id: Letter ID")
        print("  - complaint_id: Related complaint")
        print("  - letter_type: notification, summon, closure, nfa, custom")
        print("  - letter_content: Full letter text")
        print("  - generated_by: Officer username")
        print("  - generated_at: Timestamp")

        cursor.close()
        conn.close()

    except Exception as e:
        print(f"ERROR: Migration failed - {e}")
        raise

if __name__ == "__main__":
    run_migration()
