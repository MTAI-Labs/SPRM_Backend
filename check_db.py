"""Quick script to check database content"""
import psycopg2
from psycopg2.extras import RealDictCursor
import os
from dotenv import load_dotenv

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

print("=" * 80)
print("COMPLAINTS")
print("=" * 80)
cursor.execute("""
    SELECT id, complaint_title, classification, status, submitted_at,
           w1h_summary, w1h_what, w1h_who, w1h_when, w1h_where, w1h_why, w1h_how
    FROM complaints
    ORDER BY id DESC
    LIMIT 5
""")
complaints = cursor.fetchall()
for c in complaints:
    print(f"\n{'='*60}")
    print(f"ID: {c['id']}")
    print(f"Title: {c['complaint_title']}")
    print(f"Status: {c['status']}")
    print(f"Classification: {c['classification']}")
    print(f"\n5W1H Status:")
    print(f"  Summary (full): {'YES (%d chars)' % len(c['w1h_summary']) if c.get('w1h_summary') else 'NULL'}")
    print(f"  WHAT: {'YES (%d chars)' % len(c['w1h_what']) if c.get('w1h_what') else 'NULL'}")
    print(f"  WHO: {'YES (%d chars)' % len(c['w1h_who']) if c.get('w1h_who') else 'NULL'}")
    print(f"  WHEN: {'YES (%d chars)' % len(c['w1h_when']) if c.get('w1h_when') else 'NULL'}")
    print(f"  WHERE: {'YES (%d chars)' % len(c['w1h_where']) if c.get('w1h_where') else 'NULL'}")
    print(f"  WHY: {'YES (%d chars)' % len(c['w1h_why']) if c.get('w1h_why') else 'NULL'}")
    print(f"  HOW: {'YES (%d chars)' % len(c['w1h_how']) if c.get('w1h_how') else 'NULL'}")

    if c.get('w1h_what'):
        print(f"\nWHAT content preview:")
        print(f"  {c['w1h_what'][:150]}...")

    print(f"\nSubmitted: {c['submitted_at']}")

print("\n" + "=" * 80)
print("CASES")
print("=" * 80)
cursor.execute("""
    SELECT id, case_number, case_title, complaint_count, status, auto_grouped, created_at
    FROM cases
    ORDER BY id DESC
    LIMIT 10
""")
cases = cursor.fetchall()
for case in cases:
    print(f"\nCase ID: {case['id']}")
    print(f"Case Number: {case['case_number']}")
    print(f"Title: {case['case_title']}")
    print(f"Complaints: {case['complaint_count']}")
    print(f"Auto-grouped: {case['auto_grouped']}")
    print(f"Status: {case['status']}")
    print(f"Created: {case['created_at']}")

print("\n" + "=" * 80)
print("CASE-COMPLAINT RELATIONSHIPS")
print("=" * 80)
cursor.execute("""
    SELECT cc.case_id, cc.complaint_id, cc.similarity_score, cc.added_by,
           c.case_number, comp.complaint_title
    FROM case_complaints cc
    JOIN cases c ON cc.case_id = c.id
    JOIN complaints comp ON cc.complaint_id = comp.id
    ORDER BY cc.case_id, cc.complaint_id
""")
relationships = cursor.fetchall()
for rel in relationships:
    print(f"Case {rel['case_number']} -> Complaint #{rel['complaint_id']}: {rel['complaint_title'][:50]}")
    print(f"  Similarity: {rel['similarity_score']}, Added by: {rel['added_by']}")

cursor.close()
conn.close()

print("\n" + "=" * 80)
print("DONE")
print("=" * 80)
