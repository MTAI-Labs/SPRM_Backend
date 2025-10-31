#!/usr/bin/env python3
"""
Run migration to add sub_sector column to complaints table
"""

import psycopg2
from psycopg2 import sql
import os
from dotenv import load_dotenv

def run_migration():
    # Load environment variables
    load_dotenv()

    # Database connection parameters
    db_params = {
        'dbname': os.getenv('DB_NAME', 'sprm_db'),
        'user': os.getenv('DB_USER', 'postgres'),
        'password': os.getenv('DB_PASSWORD', 'postgres'),
        'host': os.getenv('DB_HOST', 'localhost'),
        'port': os.getenv('DB_PORT', '5432')
    }

    try:
        # Connect to database
        conn = psycopg2.connect(**db_params)
        conn.autocommit = True
        cursor = conn.cursor()

        print(f"Connected to database: {db_params['dbname']}")

        # Read and execute migration SQL
        with open('add_subsector_migration.sql', 'r', encoding='utf-8') as f:
            migration_sql = f.read()

        cursor.execute(migration_sql)

        print("SUCCESS: Sub-sector column added")
        print("\nChanges:")
        print("  - sub_sector column added (VARCHAR 255)")
        print("  - Index created for faster filtering")
        print("\nAI will now generate both:")
        print("  1. Main Sector (1 of 10)")
        print("  2. Sub Sector (1 of 21)")
        print("\nFrom: list_of_sectors.txt")

        cursor.close()
        conn.close()

    except Exception as e:
        print(f"ERROR: Migration failed")
        print(f"Error: {e}")
        raise

if __name__ == "__main__":
    run_migration()
