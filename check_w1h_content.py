"""Check what's actually in the w1h_summary field"""
import psycopg2
from psycopg2.extras import RealDictCursor
import os
from dotenv import load_dotenv
import json

load_dotenv()

# Connect to database
conn = psycopg2.connect(
    host=os.getenv("DB_HOST", "localhost"),
    port=os.getenv("DB_PORT", "5432"),
    database=os.getenv("DB_NAME", "sprm_db"),
    user=os.getenv("DB_USER", "postgres"),
    password=os.getenv("DB_PASSWORD", "postgres")
)

cursor = conn.cursor(cursor_factory=RealDictCursor)

# Get the latest complaint
cursor.execute("""
    SELECT id, complaint_title, w1h_summary
    FROM complaints
    WHERE w1h_summary IS NOT NULL
    ORDER BY id DESC
    LIMIT 1
""")

complaint = cursor.fetchone()

if complaint:
    print(f"Complaint ID: {complaint['id']}")
    print(f"Title: {complaint['complaint_title']}")
    print(f"\nw1h_summary type: {type(complaint['w1h_summary'])}")
    print(f"w1h_summary length: {len(complaint['w1h_summary'])}")
    print(f"\nw1h_summary content:")
    print("=" * 80)
    print(complaint['w1h_summary'])
    print("=" * 80)

    # Try to parse as JSON
    print("\nTrying to parse as JSON...")
    try:
        parsed = json.loads(complaint['w1h_summary'])
        print("✅ Successfully parsed as JSON!")
        print(f"Keys: {parsed.keys()}")
        for key, value in parsed.items():
            print(f"\n{key.upper()}:")
            print(f"  {value[:100]}..." if len(str(value)) > 100 else f"  {value}")
    except json.JSONDecodeError as e:
        print(f"❌ Not valid JSON: {e}")
        print("\nFirst 500 characters:")
        print(complaint['w1h_summary'][:500])
else:
    print("No complaints with w1h_summary found")

cursor.close()
conn.close()
