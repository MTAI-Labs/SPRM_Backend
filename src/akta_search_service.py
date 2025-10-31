"""
Akta Section Search Service - RAG-based semantic search for legislation sections
"""
import numpy as np
from typing import List, Dict, Optional
from sentence_transformers import SentenceTransformer
from database import db


class AktaSearchService:
    """Service for semantic search of akta sections using RAG"""

    def __init__(self, model_name: str = "sentence-transformers/all-MiniLM-L6-v2"):
        """
        Initialize Akta Search Service

        Args:
            model_name: Name of sentence transformer model
        """
        self.model_name = model_name
        self.model = None
        self.embedding_dim = 384  # Dimension for all-MiniLM-L6-v2

    def load_model(self):
        """Load the sentence transformer model"""
        if self.model is None:
            print(f"Loading embedding model: {self.model_name}")
            self.model = SentenceTransformer(self.model_name)
            print(f"✅ Model loaded successfully")

    def generate_embedding(self, text: str) -> np.ndarray:
        """
        Generate embedding for text

        Args:
            text: Input text

        Returns:
            Numpy array of embedding
        """
        if self.model is None:
            self.load_model()

        # Generate embedding
        embedding = self.model.encode(text, convert_to_numpy=True)
        return embedding

    def add_section(self, section_code: str, section_title: str,
                   description: str = None, category: str = None,
                   act_name: str = None) -> bool:
        """
        Add a new akta section to database with embedding

        Args:
            section_code: Section code (e.g., "Seksyen 161")
            section_title: Section title in Malay
            description: Optional detailed description
            category: Category (e.g., "Rasuah", "Pemalsuan")
            act_name: Act name (e.g., "Kanun Keseksaan")

        Returns:
            True if successful
        """
        # Generate text for embedding
        embed_text = f"{section_code} {section_title}"
        if description:
            embed_text += f" {description}"

        # Generate embedding
        embedding = self.generate_embedding(embed_text)

        # Insert to database
        query = """
        INSERT INTO akta_sections (section_code, section_title, description, category, act_name, embedding)
        VALUES (%s, %s, %s, %s, %s, %s)
        ON CONFLICT (section_code) DO UPDATE
        SET section_title = EXCLUDED.section_title,
            description = EXCLUDED.description,
            category = EXCLUDED.category,
            act_name = EXCLUDED.act_name,
            embedding = EXCLUDED.embedding,
            updated_at = CURRENT_TIMESTAMP
        """

        try:
            with db.get_cursor() as cursor:
                cursor.execute(query, (
                    section_code,
                    section_title,
                    description,
                    category,
                    act_name,
                    embedding.tolist()
                ))
            return True
        except Exception as e:
            print(f"❌ Error adding section {section_code}: {e}")
            return False

    def search_similar_sections(self, query_text: str, top_k: int = 8) -> List[Dict]:
        """
        Search for similar akta sections using semantic similarity

        Args:
            query_text: Complaint text or description
            top_k: Number of top results to return

        Returns:
            List of similar sections with scores
        """
        # Generate embedding for query
        query_embedding = self.generate_embedding(query_text)

        # Search in database using cosine similarity
        query = """
        SELECT
            id,
            section_code,
            section_title,
            description,
            category,
            act_name,
            1 - (embedding <=> %s::vector) as similarity_score
        FROM akta_sections
        ORDER BY embedding <=> %s::vector
        LIMIT %s
        """

        try:
            with db.get_cursor() as cursor:
                cursor.execute(query, (
                    query_embedding.tolist(),
                    query_embedding.tolist(),
                    top_k
                ))
                results = cursor.fetchall()

            return results

        except Exception as e:
            print(f"❌ Error searching sections: {e}")
            return []

    def get_section_by_code(self, section_code: str) -> Optional[Dict]:
        """Get specific section by code"""
        query = """
        SELECT id, section_code, section_title, description, category, act_name
        FROM akta_sections
        WHERE section_code = %s
        """

        with db.get_cursor() as cursor:
            cursor.execute(query, (section_code,))
            return cursor.fetchone()

    def get_all_sections(self) -> List[Dict]:
        """Get all sections"""
        query = """
        SELECT id, section_code, section_title, description, category, act_name
        FROM akta_sections
        ORDER BY section_code
        """

        with db.get_cursor() as cursor:
            cursor.execute(query)
            return cursor.fetchall()

    def count_sections(self) -> int:
        """Count total sections in database"""
        query = "SELECT COUNT(*) as count FROM akta_sections"

        with db.get_cursor() as cursor:
            cursor.execute(query)
            result = cursor.fetchone()
            return result['count'] if result else 0
