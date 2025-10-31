"""
Simple Akta Section Service - Category-based approach (no embeddings)
"""
from typing import List, Dict, Optional
from database import db


class AktaSimpleService:
    """Service for akta section lookup by category"""

    def __init__(self):
        """Initialize service"""
        pass

    def add_section(self, section_code: str, section_title: str,
                   category: str = None, act_name: str = None) -> bool:
        """
        Add a new akta section to database

        Args:
            section_code: Section code (e.g., "Seksyen 161")
            section_title: Section title in Malay
            category: Category (e.g., "Rasuah & Suapan")
            act_name: Act name (e.g., "Kanun Keseksaan")

        Returns:
            True if successful
        """
        query = """
        INSERT INTO akta_sections (section_code, section_title, category, act_name)
        VALUES (%s, %s, %s, %s)
        ON CONFLICT (section_code) DO UPDATE
        SET section_title = EXCLUDED.section_title,
            category = EXCLUDED.category,
            act_name = EXCLUDED.act_name
        """

        try:
            with db.get_cursor() as cursor:
                cursor.execute(query, (
                    section_code,
                    section_title,
                    category,
                    act_name or 'Kanun Keseksaan'
                ))
            return True
        except Exception as e:
            print(f"Error adding section {section_code}: {e}")
            return False

    def get_sections_by_category(self, category: str) -> List[Dict]:
        """
        Get all sections in a category

        Args:
            category: Category name

        Returns:
            List of sections
        """
        query = """
        SELECT section_code, section_title, category, act_name
        FROM akta_sections
        WHERE category = %s
        ORDER BY section_code
        """

        try:
            with db.get_cursor() as cursor:
                cursor.execute(query, (category,))
                return cursor.fetchall()
        except Exception as e:
            print(f"Error getting sections for category {category}: {e}")
            return []

    def get_all_categories(self) -> List[str]:
        """Get list of all unique categories"""
        query = """
        SELECT DISTINCT category
        FROM akta_sections
        WHERE category IS NOT NULL
        ORDER BY category
        """

        try:
            with db.get_cursor() as cursor:
                cursor.execute(query)
                results = cursor.fetchall()
                return [r['category'] for r in results]
        except Exception as e:
            print(f"Error getting categories: {e}")
            return []

    def get_all_sections(self) -> List[Dict]:
        """Get all sections"""
        query = """
        SELECT section_code, section_title, category, act_name
        FROM akta_sections
        ORDER BY category, section_code
        """

        try:
            with db.get_cursor() as cursor:
                cursor.execute(query)
                return cursor.fetchall()
        except Exception as e:
            print(f"Error getting all sections: {e}")
            return []

    def count_sections(self) -> int:
        """Count total sections"""
        query = "SELECT COUNT(*) as count FROM akta_sections"

        try:
            with db.get_cursor() as cursor:
                cursor.execute(query)
                result = cursor.fetchone()
                return result['count'] if result else 0
        except Exception as e:
            print(f"Error counting sections: {e}")
            return 0

    def get_category_summary(self) -> List[Dict]:
        """Get summary of sections per category"""
        query = """
        SELECT category, COUNT(*) as section_count
        FROM akta_sections
        WHERE category IS NOT NULL
        GROUP BY category
        ORDER BY category
        """

        try:
            with db.get_cursor() as cursor:
                cursor.execute(query)
                return cursor.fetchall()
        except Exception as e:
            print(f"Error getting category summary: {e}")
            return []
