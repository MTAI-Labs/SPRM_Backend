#!/usr/bin/env python3
"""Run migration to change akta column from VARCHAR(200) to TEXT"""

import psycopg2
import os
from dotenv import load_dotenv

def run_migration():
    load_dotenv()

    db_params = {
        'dbname': os.getenv('DB_NAME', 'sprm_db'),
        'user': os.getenv('DB_USER', 'postgres'),
        'password': os.getenv('DB_PASSWORD', 'postgres'),
        'host': os.getenv('DB_HOST', 'localhost'),
        'port': os.getenv('DB_PORT', '5432')
    }

    try:
        conn = psycopg2.connect(**db_params)
        conn.autocommit = True
        cursor = conn.cursor()

        print(f"Connected to database: {db_params['dbname']}")

        with open('fix_akta_column_migration.sql', 'r', encoding='utf-8') as f:
            migration_sql = f.read()

        cursor.execute(migration_sql)

        print("SUCCESS: akta column fixed")
        print("\nChanges:")
        print("  - akta: VARCHAR(200) → TEXT (no length limit)")
        print("\nAI can now generate longer AKTA names without truncation errors.")

        cursor.close()
        conn.close()

    except Exception as e:
        print(f"ERROR: Migration failed - {e}")
        raise

if __name__ == "__main__":
    run_migration()
