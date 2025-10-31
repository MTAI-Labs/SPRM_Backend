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

# Check w1h column types
cursor.execute("""
    SELECT column_name, data_type, character_maximum_length
    FROM information_schema.columns
    WHERE table_name = 'complaints'
    AND column_name LIKE 'w1h_%'
    ORDER BY column_name
""")

print("W1H Column Types:")
for row in cursor.fetchall():
    print(f"  {row[0]}: {row[1]}({row[2]})")

cursor.close()
conn.close()
