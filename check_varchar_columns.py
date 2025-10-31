import psycopg2
import os
from dotenv import load_dotenv

load_dotenv()

conn = psycopg2.connect(
    dbname=os.getenv('DB_NAME', 'sprm_db'),
    user=os.getenv('DB_USER', 'postgres'),
    password=os.getenv('DB_PASSWORD'),
    host=os.getenv('DB_HOST', 'localhost'),
    port=os.getenv('DB_PORT', '5432')
)

cursor = conn.cursor()

# Check varchar columns
cursor.execute("""
    SELECT column_name, data_type, character_maximum_length
    FROM information_schema.columns
    WHERE table_name = 'complaints'
    AND data_type = 'character varying'
    ORDER BY character_maximum_length, column_name
""")

print("VARCHAR Columns in complaints table:")
for row in cursor.fetchall():
    print(f"  {row[0]}: VARCHAR({row[2]})")

cursor.close()
conn.close()
