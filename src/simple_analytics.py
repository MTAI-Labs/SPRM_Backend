"""
Simple Analytics - Update analytics tables directly from complaint data
No caching, no complexity - just store counts in database
"""
from database import db
import json
import re
from collections import Counter


def update_analytics_for_complaint(complaint_id: int):
    """
    Update analytics tables after a complaint is processed

    This function:
    1. Reads complaint data from database
    2. Extracts entities, keywords, sector
    3. Updates analytics tables (increment counts)
    4. Updates overall summary

    Args:
        complaint_id: ID of complaint to analyze
    """
    try:
        print(f"📊 Updating analytics for complaint {complaint_id}...")

        # Get complaint data
        with db.get_cursor() as cursor:
            cursor.execute("""
                SELECT
                    extracted_data,
                    sector,
                    classification,
                    officer_status,
                    w1h_summary
                FROM complaints
                WHERE id = %s
            """, (complaint_id,))
            complaint = cursor.fetchone()

        if not complaint:
            print(f"⚠️  Complaint {complaint_id} not found")
            return

        extracted_data = complaint.get('extracted_data') or {}
        sector = complaint.get('sector')
        classification = complaint.get('classification')
        officer_status = complaint.get('officer_status')
        w1h_summary = complaint.get('w1h_summary') or ''

        # 1. Update entities (names, orgs, locations, amounts)
        entities = extracted_data.get('entities', {})
        _update_entities('name', entities.get('names', []))
        _update_entities('organization', entities.get('organizations', []))
        _update_entities('location', entities.get('locations', []))
        _update_entities('amount', entities.get('amounts', []))

        # 2. Update sector counts
        if sector:
            _update_sector(sector, classification)

        # 3. Update keyword patterns
        _update_patterns(w1h_summary)

        # 4. Update overall summary
        _update_summary(classification, officer_status)

        print(f"✅ Analytics updated for complaint {complaint_id}")

    except Exception as e:
        print(f"❌ Error updating analytics for complaint {complaint_id}: {e}")


def _update_entities(entity_type: str, entity_list: list):
    """Update entity counts in analytics_entities table"""
    if not entity_list:
        return

    try:
        with db.get_cursor() as cursor:
            for entity in entity_list:
                if not entity or not str(entity).strip():
                    continue

                entity_value = str(entity).strip()[:500]  # Limit length

                cursor.execute("""
                    INSERT INTO analytics_entities (entity_type, entity_value, count)
                    VALUES (%s, %s, 1)
                    ON CONFLICT (entity_type, entity_value)
                    DO UPDATE SET
                        count = analytics_entities.count + 1,
                        last_updated = CURRENT_TIMESTAMP
                """, (entity_type, entity_value))
    except Exception as e:
        print(f"⚠️  Error updating entities: {e}")


def _update_sector(sector: str, classification: str):
    """Update sector statistics in analytics_sectors table"""
    if not sector:
        return

    try:
        # Determine YES/NO increment
        yes_inc = 1 if classification == 'YES' else 0
        no_inc = 1 if classification == 'NO' else 0

        with db.get_cursor() as cursor:
            cursor.execute("""
                INSERT INTO analytics_sectors (sector, complaint_count, yes_count, no_count)
                VALUES (%s, 1, %s, %s)
                ON CONFLICT (sector)
                DO UPDATE SET
                    complaint_count = analytics_sectors.complaint_count + 1,
                    yes_count = analytics_sectors.yes_count + %s,
                    no_count = analytics_sectors.no_count + %s,
                    last_updated = CURRENT_TIMESTAMP
            """, (sector, yes_inc, no_inc, yes_inc, no_inc))
    except Exception as e:
        print(f"⚠️  Error updating sector: {e}")


def _update_patterns(text: str):
    """Extract and update keyword patterns (2-word combinations)"""
    if not text:
        return

    try:
        # Extract keywords (simple approach)
        words = re.findall(r'\b[a-zA-Z]{4,}\b', text.lower())

        # Remove common words
        stopwords = {'yang', 'dengan', 'untuk', 'pada', 'dari', 'adalah', 'akan',
                     'telah', 'oleh', 'this', 'that', 'with', 'from', 'have', 'been'}
        keywords = [w for w in words if w not in stopwords]

        # Get 2-word patterns
        patterns = []
        for i in range(len(keywords) - 1):
            k1, k2 = sorted([keywords[i], keywords[i+1]])  # Sort for consistency
            patterns.append((k1, k2))

        # Count patterns
        pattern_counts = Counter(patterns)

        # Only store patterns that appear at least once
        with db.get_cursor() as cursor:
            for (k1, k2), count in pattern_counts.most_common(10):  # Top 10 patterns
                cursor.execute("""
                    INSERT INTO analytics_patterns (keyword1, keyword2, count)
                    VALUES (%s, %s, 1)
                    ON CONFLICT (keyword1, keyword2)
                    DO UPDATE SET
                        count = analytics_patterns.count + 1,
                        last_updated = CURRENT_TIMESTAMP
                """, (k1, k2))
    except Exception as e:
        print(f"⚠️  Error updating patterns: {e}")


def _update_summary(classification: str, officer_status: str):
    """Update overall summary statistics"""
    try:
        # Determine increments
        yes_inc = 1 if classification == 'YES' else 0
        no_inc = 1 if classification == 'NO' else 0
        pending_inc = 1 if officer_status == 'pending_review' else 0
        nfa_inc = 1 if officer_status == 'nfa' else 0
        escalated_inc = 1 if officer_status == 'escalated' else 0

        with db.get_cursor() as cursor:
            cursor.execute("""
                UPDATE analytics_summary
                SET
                    total_complaints = total_complaints + 1,
                    yes_classification_count = yes_classification_count + %s,
                    no_classification_count = no_classification_count + %s,
                    pending_review_count = pending_review_count + %s,
                    nfa_count = nfa_count + %s,
                    escalated_count = escalated_count + %s,
                    last_updated = CURRENT_TIMESTAMP
                WHERE id = 1
            """, (yes_inc, no_inc, pending_inc, nfa_inc, escalated_inc))

            # Also update case count
            cursor.execute("SELECT COUNT(*) as count FROM cases")
            case_count = cursor.fetchone()['count']

            cursor.execute("""
                UPDATE analytics_summary
                SET total_cases = %s
                WHERE id = 1
            """, (case_count,))
    except Exception as e:
        print(f"⚠️  Error updating summary: {e}")


def get_simple_analytics():
    """
    Get pre-computed analytics from database tables
    Fast and simple - just read from tables

    Returns:
        dict: Analytics data ready for frontend
    """
    try:
        result = {}

        with db.get_cursor() as cursor:
            # 1. Overall summary
            cursor.execute("SELECT * FROM analytics_summary WHERE id = 1")
            summary = cursor.fetchone()
            result['summary'] = dict(summary) if summary else {}

            # 2. Top entities
            cursor.execute("""
                SELECT entity_type, entity_value, count
                FROM analytics_entities
                ORDER BY count DESC, entity_value
                LIMIT 50
            """)
            entities = cursor.fetchall()

            # Group by type
            result['top_names'] = [{'name': e['entity_value'], 'count': e['count']}
                                   for e in entities if e['entity_type'] == 'name'][:10]
            result['top_organizations'] = [{'organization': e['entity_value'], 'count': e['count']}
                                          for e in entities if e['entity_type'] == 'organization'][:10]
            result['top_locations'] = [{'location': e['entity_value'], 'count': e['count']}
                                      for e in entities if e['entity_type'] == 'location'][:10]
            result['top_amounts'] = [{'amount': e['entity_value'], 'count': e['count']}
                                    for e in entities if e['entity_type'] == 'amount'][:10]

            # 3. Sector breakdown
            cursor.execute("""
                SELECT sector, complaint_count, yes_count, no_count
                FROM analytics_sectors
                ORDER BY complaint_count DESC
                LIMIT 20
            """)
            result['sectors'] = [dict(row) for row in cursor.fetchall()]

            # 4. Top patterns
            cursor.execute("""
                SELECT keyword1, keyword2, count
                FROM analytics_patterns
                ORDER BY count DESC
                LIMIT 20
            """)
            result['patterns'] = [
                {
                    'pattern': f"{row['keyword1']} + {row['keyword2']}",
                    'count': row['count']
                }
                for row in cursor.fetchall()
            ]

        return result

    except Exception as e:
        print(f"❌ Error getting analytics: {e}")
        return {
            'summary': {},
            'top_names': [],
            'top_organizations': [],
            'top_locations': [],
            'top_amounts': [],
            'sectors': [],
            'patterns': []
        }
