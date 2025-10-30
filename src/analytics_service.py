"""
Analytics Service for SPRM Backend
====================================
Provides meaningful analytics and pattern detection for corruption complaints.

Key Features:
- Entity-based analytics (who, what, where, items involved)
- Pattern detection (tender + gold, school + bribery)
- Trending analysis
- Case-level insights
- AI-powered insight generation
"""

from typing import Dict, List, Optional, Any
from collections import Counter, defaultdict
from datetime import datetime, timedelta
from database import db
import json
import re
import time


class AnalyticsService:
    """Service for generating analytics and insights from complaints"""

    def __init__(self, openrouter_service=None):
        """
        Initialize analytics service

        Args:
            openrouter_service: OpenRouter service for AI-powered insights
        """
        self.openrouter_service = openrouter_service
        # In-memory cache for quick access
        self._memory_cache = {}
        self._cache_ttl = 300  # 5 minutes default TTL for memory cache

    def _get_from_cache(self, cache_key: str) -> Optional[Dict]:
        """
        Get analytics from cache (memory or database)

        Args:
            cache_key: Cache key (e.g., 'dashboard_30d')

        Returns:
            Cached data or None if not found/expired
        """
        # Check memory cache first
        if cache_key in self._memory_cache:
            cached_item = self._memory_cache[cache_key]
            if time.time() < cached_item['expires_at']:
                print(f"✅ Cache HIT (memory): {cache_key}")
                return cached_item['data']
            else:
                # Expired, remove from memory
                del self._memory_cache[cache_key]

        # Check database cache
        query = """
        SELECT cache_data, expires_at
        FROM analytics_cache
        WHERE cache_key = %s
        AND expires_at > CURRENT_TIMESTAMP
        """

        try:
            with db.get_cursor() as cursor:
                cursor.execute(query, (cache_key,))
                result = cursor.fetchone()

                if result:
                    print(f"✅ Cache HIT (database): {cache_key}")
                    # Store in memory cache for next time
                    expires_at_ts = result['expires_at'].timestamp()
                    self._memory_cache[cache_key] = {
                        'data': result['cache_data'],
                        'expires_at': expires_at_ts
                    }
                    return result['cache_data']
        except Exception as e:
            print(f"⚠️  Cache read error: {e}")

        print(f"❌ Cache MISS: {cache_key}")
        return None

    def _save_to_cache(self, cache_key: str, data: Dict, ttl_seconds: int = 3600, period_days: int = None):
        """
        Save analytics to cache (both memory and database)

        Args:
            cache_key: Cache key (e.g., 'dashboard_30d')
            data: Analytics data to cache
            ttl_seconds: Time to live in seconds (default: 1 hour)
            period_days: Period analyzed (for metadata)
        """
        expires_at = datetime.now() + timedelta(seconds=ttl_seconds)
        expires_at_ts = expires_at.timestamp()

        # Save to memory cache
        self._memory_cache[cache_key] = {
            'data': data,
            'expires_at': expires_at_ts
        }

        # Save to database cache
        query = """
        INSERT INTO analytics_cache (cache_key, cache_data, period_days, expires_at, complaint_count)
        VALUES (%s, %s, %s, %s, %s)
        ON CONFLICT (cache_key)
        DO UPDATE SET
            cache_data = EXCLUDED.cache_data,
            period_days = EXCLUDED.period_days,
            computed_at = CURRENT_TIMESTAMP,
            expires_at = EXCLUDED.expires_at,
            complaint_count = EXCLUDED.complaint_count
        """

        try:
            complaint_count = data.get('total_complaints_analyzed') or data.get('entity_analytics', {}).get('total_complaints_analyzed', 0)

            with db.get_cursor() as cursor:
                cursor.execute(query, (
                    cache_key,
                    json.dumps(data),
                    period_days,
                    expires_at,
                    complaint_count
                ))

            print(f"💾 Cached: {cache_key} (TTL: {ttl_seconds}s)")
        except Exception as e:
            print(f"⚠️  Cache write error: {e}")

    def invalidate_cache(self, pattern: str = None):
        """
        Invalidate cache entries

        Args:
            pattern: If provided, only invalidate keys matching pattern
                    If None, clear all cache
        """
        # Clear memory cache
        if pattern:
            keys_to_delete = [k for k in self._memory_cache.keys() if pattern in k]
            for key in keys_to_delete:
                del self._memory_cache[key]
            print(f"🗑️  Cleared memory cache matching: {pattern}")
        else:
            self._memory_cache.clear()
            print("🗑️  Cleared all memory cache")

        # Clear database cache
        if pattern:
            query = "DELETE FROM analytics_cache WHERE cache_key LIKE %s"
            param = f"%{pattern}%"
        else:
            query = "DELETE FROM analytics_cache"
            param = None

        try:
            with db.get_cursor() as cursor:
                if param:
                    cursor.execute(query, (param,))
                else:
                    cursor.execute(query)
                print(f"🗑️  Cleared database cache")
        except Exception as e:
            print(f"⚠️  Cache invalidation error: {e}")

    def get_entity_analytics(self, date_from: Optional[datetime] = None,
                            date_to: Optional[datetime] = None) -> Dict:
        """
        Extract and analyze entities from complaints

        Returns:
        - Top names mentioned
        - Top organizations/departments
        - Top locations
        - Top amounts/items (gold, cash, contracts)
        """
        query = """
        SELECT
            id,
            extracted_data,
            w1h_who,
            w1h_where,
            sector,
            category,
            submitted_at
        FROM complaints
        WHERE status = 'processed'
        """
        params = []

        if date_from:
            query += " AND submitted_at >= %s"
            params.append(date_from)

        if date_to:
            query += " AND submitted_at <= %s"
            params.append(date_to)

        with db.get_cursor() as cursor:
            cursor.execute(query, tuple(params))
            complaints = cursor.fetchall()

        # Collect entities
        names = []
        organizations = []
        locations = []
        amounts = []
        sectors_count = Counter()
        categories_count = Counter()

        for complaint in complaints:
            # From extracted_data
            if complaint.get('extracted_data'):
                entities = complaint['extracted_data'].get('entities', {})
                names.extend(entities.get('names', []))
                organizations.extend(entities.get('organizations', []))
                locations.extend(entities.get('locations', []))
                amounts.extend(entities.get('amounts', []))

            # From 5W1H
            if complaint.get('w1h_who'):
                # Extract names from who field
                names.extend(self._extract_names_from_text(complaint['w1h_who']))

            if complaint.get('w1h_where'):
                locations.extend(self._extract_locations_from_text(complaint['w1h_where']))

            # Count sectors and categories
            if complaint.get('sector'):
                sectors_count[complaint['sector']] += 1

            if complaint.get('category'):
                categories_count[complaint['category']] += 1

        # Count and rank
        names_counter = Counter([n.strip() for n in names if n and len(n.strip()) > 2])
        orgs_counter = Counter([o.strip() for o in organizations if o and len(o.strip()) > 2])
        locations_counter = Counter([l.strip() for l in locations if l and len(l.strip()) > 2])
        amounts_counter = Counter([a.strip() for a in amounts if a and len(a.strip()) > 0])

        return {
            "total_complaints_analyzed": len(complaints),
            "top_names": [{"name": name, "count": count} for name, count in names_counter.most_common(10)],
            "top_organizations": [{"org": org, "count": count} for org, count in orgs_counter.most_common(10)],
            "top_locations": [{"location": loc, "count": count} for loc, count in locations_counter.most_common(10)],
            "top_amounts": [{"amount": amt, "count": count} for amt, count in amounts_counter.most_common(10)],
            "sectors": [{"sector": sector, "count": count} for sector, count in sectors_count.most_common()],
            "categories": [{"category": cat, "count": count} for cat, count in categories_count.most_common()]
        }

    def detect_patterns(self, min_occurrences: int = 2) -> Dict:
        """
        Detect common patterns and combinations in complaints

        Examples:
        - "tender + gold" appears 3 times
        - "school + bribery" appears 4 times
        - "cash payment + officer" appears 2 times
        """
        query = """
        SELECT
            id,
            complaint_description,
            extracted_data,
            w1h_what,
            w1h_how,
            sector,
            category
        FROM complaints
        WHERE status = 'processed'
        """

        with db.get_cursor() as cursor:
            cursor.execute(query)
            complaints = cursor.fetchall()

        # Extract keywords from each complaint
        complaint_keywords = []

        for complaint in complaints:
            keywords = set()

            # Extract from description
            desc = complaint.get('complaint_description', '')
            keywords.update(self._extract_corruption_keywords(desc))

            # Extract from 5W1H
            if complaint.get('w1h_what'):
                keywords.update(self._extract_corruption_keywords(complaint['w1h_what']))

            if complaint.get('w1h_how'):
                keywords.update(self._extract_corruption_keywords(complaint['w1h_how']))

            # Add sector and category
            if complaint.get('sector'):
                keywords.add(complaint['sector'].lower())

            if complaint.get('category'):
                keywords.add(complaint['category'].lower())

            # Extract entities
            if complaint.get('extracted_data'):
                entities = complaint['extracted_data'].get('entities', {})

                # Add amounts/items
                for amt in entities.get('amounts', []):
                    if 'gold' in amt.lower() or 'emas' in amt.lower():
                        keywords.add('gold')
                    if 'cash' in amt.lower() or 'tunai' in amt.lower() or 'rm' in amt.lower():
                        keywords.add('cash')

            complaint_keywords.append({
                'id': complaint['id'],
                'keywords': list(keywords)
            })

        # Find combinations (2-keyword and 3-keyword patterns)
        pattern_2 = Counter()
        pattern_3 = Counter()

        for item in complaint_keywords:
            keywords = sorted(item['keywords'])  # Sort for consistent ordering

            # 2-keyword combinations
            for i in range(len(keywords)):
                for j in range(i + 1, len(keywords)):
                    pattern_2[f"{keywords[i]} + {keywords[j]}"] += 1

            # 3-keyword combinations
            for i in range(len(keywords)):
                for j in range(i + 1, len(keywords)):
                    for k in range(j + 1, len(keywords)):
                        pattern_3[f"{keywords[i]} + {keywords[j]} + {keywords[k]}"] += 1

        # Filter by minimum occurrences
        significant_2 = [(pattern, count) for pattern, count in pattern_2.items() if count >= min_occurrences]
        significant_3 = [(pattern, count) for pattern, count in pattern_3.items() if count >= min_occurrences]

        # Sort by count
        significant_2.sort(key=lambda x: x[1], reverse=True)
        significant_3.sort(key=lambda x: x[1], reverse=True)

        return {
            "two_keyword_patterns": [
                {"pattern": pattern, "count": count, "example": f"{count} complaints involve both {pattern}"}
                for pattern, count in significant_2[:20]
            ],
            "three_keyword_patterns": [
                {"pattern": pattern, "count": count, "example": f"{count} complaints involve {pattern}"}
                for pattern, count in significant_3[:10]
            ],
            "total_complaints_analyzed": len(complaints)
        }

    def get_trending_keywords(self, days: int = 30, top_n: int = 20) -> Dict:
        """
        Get trending keywords over specified time period

        Args:
            days: Number of days to analyze (default: 30)
            top_n: Number of top keywords to return

        Returns:
            Top keywords with counts and trend direction
        """
        date_from = datetime.now() - timedelta(days=days)

        query = """
        SELECT
            complaint_description,
            w1h_what,
            w1h_how,
            sector,
            category,
            submitted_at
        FROM complaints
        WHERE status = 'processed'
        AND submitted_at >= %s
        ORDER BY submitted_at DESC
        """

        with db.get_cursor() as cursor:
            cursor.execute(query, (date_from,))
            complaints = cursor.fetchall()

        # Extract all keywords
        all_keywords = []

        for complaint in complaints:
            keywords = set()

            # Extract from description
            desc = complaint.get('complaint_description', '')
            keywords.update(self._extract_corruption_keywords(desc))

            # Extract from 5W1H
            if complaint.get('w1h_what'):
                keywords.update(self._extract_corruption_keywords(complaint['w1h_what']))

            if complaint.get('w1h_how'):
                keywords.update(self._extract_corruption_keywords(complaint['w1h_how']))

            all_keywords.extend(list(keywords))

        keyword_counts = Counter(all_keywords)
        top_keywords = keyword_counts.most_common(top_n)

        return {
            "period_days": days,
            "total_complaints": len(complaints),
            "trending_keywords": [
                {"keyword": keyword, "count": count, "percentage": round((count / len(complaints)) * 100, 1)}
                for keyword, count in top_keywords
            ]
        }

    def get_case_analytics(self) -> Dict:
        """
        Get analytics at the case level

        Returns:
        - Largest cases by complaint count
        - Cases by status, priority, classification
        - Average complaints per case
        """
        query = """
        SELECT
            id,
            case_number,
            case_title,
            complaint_count,
            classification,
            priority,
            status,
            created_at
        FROM cases
        ORDER BY complaint_count DESC
        """

        with db.get_cursor() as cursor:
            cursor.execute(query)
            cases = cursor.fetchall()

        if not cases:
            return {
                "total_cases": 0,
                "total_complaints_in_cases": 0,
                "message": "No cases found"
            }

        # Calculate statistics
        total_complaints = sum(case['complaint_count'] for case in cases)
        avg_complaints = total_complaints / len(cases) if cases else 0

        # Group by status, priority, classification
        by_status = Counter(case['status'] for case in cases)
        by_priority = Counter(case['priority'] for case in cases)
        by_classification = Counter(case['classification'] for case in cases if case['classification'])

        # Top 10 largest cases
        largest_cases = cases[:10]

        return {
            "total_cases": len(cases),
            "total_complaints_in_cases": total_complaints,
            "average_complaints_per_case": round(avg_complaints, 2),
            "by_status": dict(by_status),
            "by_priority": dict(by_priority),
            "by_classification": dict(by_classification),
            "largest_cases": [
                {
                    "case_number": case['case_number'],
                    "case_title": case['case_title'],
                    "complaint_count": case['complaint_count'],
                    "classification": case['classification'],
                    "priority": case['priority'],
                    "status": case['status']
                }
                for case in largest_cases
            ]
        }

    def generate_ai_insights(self, analytics_data: Dict) -> Optional[str]:
        """
        Use AI to generate natural language insights from analytics data

        Args:
            analytics_data: Dict containing entity analytics, patterns, etc.

        Returns:
            Natural language summary of key findings
        """
        if not self.openrouter_service:
            return None

        # Build context from analytics
        context = json.dumps(analytics_data, indent=2, ensure_ascii=False)

        prompt = f"""Anda adalah penganalisis data SPRM yang mahir. Berdasarkan data analitik aduan rasuah di bawah, hasilkan RINGKASAN INSIGHT yang berguna untuk pegawai SPRM.

**Data Analitik:**
{context}

**Tugasan:**
Hasilkan ringkasan insight dalam 4-6 ayat yang merangkumi:
1. Pola atau trend utama yang ditemui
2. Entiti (nama, organisasi, lokasi) yang paling kerap disebut
3. Kombinasi corruption yang biasa (contoh: tender + gold, school + bribery)
4. Cadangan tindakan atau fokus untuk siasatan

**Format:**
- Gunakan Bahasa Malaysia formal dan profesional
- Fokus kepada insight yang boleh diambil tindakan (actionable)
- Highlight pola yang tidak normal atau membimbangkan
- Berikan konteks statistik (contoh: "3 aduan melibatkan tender + emas")

Insight sahaja, tanpa tajuk:"""

        result = self.openrouter_service.call_openrouter(
            prompt=prompt,
            max_tokens=800,
            temperature=0.5
        )

        if result:
            return result.strip()

        return None

    def get_comprehensive_dashboard(self, days: int = 30, use_cache: bool = True) -> Dict:
        """
        Get comprehensive analytics for dashboard (WITH CACHING)

        Combines:
        - Entity analytics
        - Pattern detection
        - Trending keywords
        - Case analytics
        - AI-generated insights

        Args:
            days: Number of days to analyze
            use_cache: Whether to use cached data (default: True)

        Returns:
            Complete analytics dashboard
        """
        # Generate cache key
        cache_key = f"dashboard_{days}d"

        # Try to get from cache first
        if use_cache:
            cached = self._get_from_cache(cache_key)
            if cached:
                return cached

        # Cache miss - compute analytics
        print(f"🔄 Computing analytics for {days} days...")
        start_time = time.time()

        date_from = datetime.now() - timedelta(days=days)

        # Gather all analytics
        entity_analytics = self.get_entity_analytics(date_from=date_from)
        patterns = self.detect_patterns(min_occurrences=2)
        trending = self.get_trending_keywords(days=days, top_n=15)
        case_analytics = self.get_case_analytics()

        # Combine for AI insight
        combined_data = {
            "entity_analytics": entity_analytics,
            "patterns": patterns,
            "trending": trending,
            "case_analytics": case_analytics
        }

        # Generate AI insights
        ai_insights = self.generate_ai_insights(combined_data)

        result = {
            "period": {
                "days": days,
                "from": date_from.isoformat(),
                "to": datetime.now().isoformat()
            },
            "entity_analytics": entity_analytics,
            "patterns": patterns,
            "trending": trending,
            "case_analytics": case_analytics,
            "ai_insights": ai_insights,
            "generated_at": datetime.now().isoformat(),
            "computation_time_seconds": round(time.time() - start_time, 2),
            "cached": False
        }

        # Save to cache (TTL: 1 hour for dashboard)
        self._save_to_cache(cache_key, result, ttl_seconds=3600, period_days=days)

        print(f"✅ Analytics computed in {result['computation_time_seconds']}s")
        return result

    def precompute_analytics(self, periods: List[int] = [7, 30, 90]):
        """
        Pre-compute analytics for common periods

        Call this periodically (e.g., every hour) to keep cache fresh

        Args:
            periods: List of day periods to pre-compute (default: [7, 30, 90])

        Returns:
            Dict with status of each computation
        """
        results = {}

        for days in periods:
            try:
                print(f"📊 Pre-computing analytics for {days} days...")
                # Force recompute by using use_cache=False
                dashboard = self.get_comprehensive_dashboard(days=days, use_cache=False)
                results[f"{days}d"] = {
                    "status": "success",
                    "computation_time": dashboard.get('computation_time_seconds'),
                    "complaint_count": dashboard['entity_analytics']['total_complaints_analyzed']
                }
            except Exception as e:
                print(f"❌ Error pre-computing {days}d analytics: {e}")
                results[f"{days}d"] = {
                    "status": "error",
                    "error": str(e)
                }

        return {
            "precomputed_periods": list(results.keys()),
            "results": results,
            "timestamp": datetime.now().isoformat()
        }

    # ============================================================================
    # Helper Methods
    # ============================================================================

    def _extract_corruption_keywords(self, text: str) -> set:
        """
        Extract corruption-related keywords from text

        Returns set of relevant keywords (lowercase)
        """
        if not text:
            return set()

        text_lower = text.lower()
        keywords = set()

        # Corruption types
        corruption_types = [
            'rasuah', 'bribery', 'suapan', 'tender', 'kontrak', 'contract',
            'abuse', 'salah guna', 'pecah amanah', 'penipuan', 'fraud',
            'kronisme', 'nepotisme', 'conflict of interest'
        ]

        # Items/methods
        items = [
            'gold', 'emas', 'cash', 'tunai', 'wang', 'money', 'rm',
            'hadiah', 'gift', 'komisyen', 'commission', 'kickback'
        ]

        # Sectors (simplified)
        sectors = [
            'pendidikan', 'education', 'sekolah', 'school',
            'kesihatan', 'health', 'hospital',
            'polis', 'police', 'imigresen', 'immigration',
            'kastam', 'customs', 'jpj', 'jkr',
            'pembinaan', 'construction', 'projek', 'project'
        ]

        all_keywords = corruption_types + items + sectors

        for keyword in all_keywords:
            if keyword in text_lower:
                # Normalize to English where possible
                normalized = self._normalize_keyword(keyword)
                keywords.add(normalized)

        return keywords

    def _normalize_keyword(self, keyword: str) -> str:
        """Normalize keywords to standard form (prefer English)"""
        mapping = {
            'rasuah': 'bribery',
            'suapan': 'bribery',
            'emas': 'gold',
            'tunai': 'cash',
            'wang': 'cash',
            'hadiah': 'gift',
            'komisyen': 'commission',
            'sekolah': 'school',
            'pendidikan': 'education',
            'kesihatan': 'health',
            'polis': 'police',
            'pembinaan': 'construction',
            'projek': 'project'
        }
        return mapping.get(keyword, keyword)

    def _extract_names_from_text(self, text: str) -> List[str]:
        """
        Extract potential names from text (basic implementation)
        """
        if not text:
            return []

        # Simple heuristic: capitalized words that are not at start of sentence
        words = text.split()
        names = []

        for i, word in enumerate(words):
            # Skip if it's likely a title or common word
            if word.lower() in ['encik', 'puan', 'tuan', 'dr', 'dato', 'tan sri', 'the', 'a', 'an']:
                continue

            # If capitalized and length > 2
            if word[0].isupper() and len(word) > 2 and i > 0:  # Not first word
                names.append(word)

        return names

    def _extract_locations_from_text(self, text: str) -> List[str]:
        """
        Extract potential locations from text
        """
        if not text:
            return []

        # Common location indicators
        location_keywords = ['di', 'at', 'in', 'dari', 'from']
        locations = []

        words = text.split()
        for i, word in enumerate(words):
            if word.lower() in location_keywords and i + 1 < len(words):
                # Get next few words as potential location
                location = ' '.join(words[i+1:i+4])
                locations.append(location)

        return locations
