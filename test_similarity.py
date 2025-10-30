"""Test similarity search functionality"""
import sys
sys.path.insert(0, 'src')

from search_relevant_case import CaseSearchEngine
from database import db

# Initialize search engine
print("🚀 Initializing search engine...")
search_engine = CaseSearchEngine()
search_engine.load_model()

# Get complaints from database
print("\n📋 Loading complaints from database...")
with db.get_cursor() as cursor:
    cursor.execute("""
        SELECT id, complaint_title, complaint_description, w1h_summary
        FROM complaints
        WHERE status = 'processed'
        ORDER BY id
    """)
    complaints = cursor.fetchall()

print(f"Found {len(complaints)} processed complaints")

# Add complaints to search engine
print("\n📥 Adding complaints to search engine...")
for complaint in complaints:
    # Combine text for better search
    text = f"{complaint['complaint_title']} {complaint['complaint_description']}"
    if complaint.get('w1h_summary'):
        text += f" {complaint['w1h_summary']}"

    search_engine.add_case(
        case_id=complaint['id'],
        description=text
    )
    print(f"  Added complaint #{complaint['id']}: {complaint['complaint_title']}")

# Test search
print("\n🔍 Testing similarity search...")
if len(complaints) >= 2:
    test_complaint = complaints[-1]  # Last complaint
    test_text = f"{test_complaint['complaint_title']} {test_complaint['complaint_description']}"

    print(f"\nSearching for similar complaints to: '{test_complaint['complaint_title']}'")

    results = search_engine.search(query_text=test_text, top_k=5)

    print(f"\n✅ Found {len(results)} similar complaints:")
    for result in results:
        print(f"  - ID {result['id']}: Similarity {result['similarity_score']:.3f}")

print("\n" + "=" * 80)
print("ANALYSIS")
print("=" * 80)

# Check if complaints should be grouped
if len(complaints) >= 2:
    similarity_threshold = 0.70
    print(f"\nSimilarity threshold for grouping: {similarity_threshold}")

    # Compare last two complaints
    c1 = complaints[-2]
    c2 = complaints[-1]

    text1 = f"{c1['complaint_title']} {c1['complaint_description']}"
    if c1.get('w1h_summary'):
        text1 += f" {c1['w1h_summary']}"

    text2 = f"{c2['complaint_title']} {c2['complaint_description']}"
    if c2.get('w1h_summary'):
        text2 += f" {c2['w1h_summary']}"

    # Search for c2 similarity to c1
    results = search_engine.search(query_text=text2, top_k=5)

    print(f"\nComplaint #{c2['id']} vs Complaint #{c1['id']}:")
    print(f"  Title 1: {c1['complaint_title']}")
    print(f"  Title 2: {c2['complaint_title']}")

    # Find c1 in results
    c1_result = next((r for r in results if r['id'] == c1['id']), None)
    if c1_result:
        similarity = c1_result['similarity_score']
        print(f"  Similarity: {similarity:.3f}")
        if similarity >= similarity_threshold:
            print(f"  ✅ Should be GROUPED (>= {similarity_threshold})")
        else:
            print(f"  ❌ Should NOT be grouped (< {similarity_threshold})")
    else:
        print(f"  ⚠️ Complaint #{c1['id']} not found in search results")

print("\n✅ Done!")
