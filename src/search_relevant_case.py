"""
Search Relevant Case System
============================
Semantic search for similar complaints using SentenceTransformer embeddings.

Features:
- Find similar complaints using cosine similarity
- Support for PostgreSQL database storage
- CSV import with automatic embedding generation
- In-memory search mode (no database required)
"""

import numpy as np
import pandas as pd
from sentence_transformers import SentenceTransformer
from sklearn.metrics.pairwise import cosine_similarity
from typing import List, Dict, Any, Optional, Tuple
import logging
import pickle
import os

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class CaseSearchEngine:
    """Search engine for finding similar complaints"""

    def __init__(self, model_name: str = 'all-MiniLM-L6-v2', use_database: bool = False, db_config: Optional[Dict] = None):
        """
        Initialize Case Search Engine

        Args:
            model_name: SentenceTransformer model name
            use_database: Whether to use PostgreSQL database
            db_config: Database configuration (if use_database=True)
        """
        self.model_name = model_name
        self.use_database = use_database
        self.db_config = db_config or {}
        self.embedding_model = None

        # In-memory storage (used when not using database)
        self.cases = []  # List of {id, description, embedding}
        self.embeddings_matrix = None

    def load_model(self):
        """Load SentenceTransformer model"""
        if self.embedding_model is None:
            logger.info(f"Loading embedding model: {self.model_name}")
            self.embedding_model = SentenceTransformer(self.model_name)
            logger.info("✅ Embedding model loaded successfully!")
        return self.embedding_model

    def combine_descriptions(self, description: str, description_1: str = None,
                           description_2: str = None, description_3: str = None,
                           description_4: str = None, description_5: str = None) -> str:
        """
        Combine multiple description fields into single text

        Args:
            description: Main description
            description_1 to description_5: Additional descriptions

        Returns:
            Combined text string
        """
        descriptions = []

        if description and description.strip():
            descriptions.append(description.strip())

        for desc in [description_1, description_2, description_3, description_4, description_5]:
            if desc and desc.strip():
                descriptions.append(desc.strip())

        return ' | '.join(descriptions) if descriptions else ""

    def generate_embedding(self, text: str) -> np.ndarray:
        """
        Generate embedding for text

        Args:
            text: Input text

        Returns:
            Embedding vector as numpy array
        """
        if self.embedding_model is None:
            self.load_model()

        embedding = self.embedding_model.encode([text], convert_to_numpy=True)
        return embedding[0]

    def add_case(self, case_id: int, description: str, **additional_descriptions) -> Dict:
        """
        Add a case to the search engine (in-memory mode)

        Args:
            case_id: Unique case ID
            description: Main description
            **additional_descriptions: Additional description fields (description_1, etc.)

        Returns:
            Case information with embedding
        """
        # Combine descriptions
        combined_text = self.combine_descriptions(description, **additional_descriptions)

        # Generate embedding
        embedding = self.generate_embedding(combined_text)

        # Store case
        case_data = {
            'id': case_id,
            'description': description,
            'combined_text': combined_text,
            'embedding': embedding
        }

        self.cases.append(case_data)

        # Rebuild embeddings matrix
        self._rebuild_embeddings_matrix()

        return case_data

    def load_cases_from_csv(self, csv_path: str, id_column: str = 'id',
                           description_column: str = 'description',
                           max_cases: Optional[int] = None) -> int:
        """
        Load cases from CSV file

        Args:
            csv_path: Path to CSV file
            id_column: Name of ID column
            description_column: Name of description column
            max_cases: Maximum number of cases to load (None for all)

        Returns:
            Number of cases loaded
        """
        logger.info(f"Loading cases from CSV: {csv_path}")

        df = pd.read_csv(csv_path)

        if max_cases:
            df = df.head(max_cases)

        logger.info(f"Processing {len(df)} cases...")

        for idx, row in df.iterrows():
            # Get description fields
            description = row.get(description_column, "")

            # Get additional description fields if they exist
            additional_desc = {}
            for i in range(1, 6):
                col_name = f'description_{i}'
                if col_name in df.columns:
                    additional_desc[col_name] = row.get(col_name, "")

            # Add case
            case_id = row.get(id_column, idx)
            self.add_case(case_id, description, **additional_desc)

            if (idx + 1) % 100 == 0:
                logger.info(f"Processed {idx + 1}/{len(df)} cases")

        logger.info(f"✅ Loaded {len(self.cases)} cases")
        return len(self.cases)

    def _rebuild_embeddings_matrix(self):
        """Rebuild embeddings matrix from cases"""
        if self.cases:
            self.embeddings_matrix = np.vstack([case['embedding'] for case in self.cases])

    def search(self, query_text: str = None, query_description: Dict = None,
               top_k: int = 5) -> List[Dict]:
        """
        Search for similar cases

        Args:
            query_text: Direct query text (if provided, query_description is ignored)
            query_description: Dictionary with description fields
            top_k: Number of top results to return

        Returns:
            List of similar cases with similarity scores
        """
        # Prepare query text
        if query_text:
            combined_query = query_text
        elif query_description:
            combined_query = self.combine_descriptions(
                description=query_description.get('description', ''),
                description_1=query_description.get('description_1'),
                description_2=query_description.get('description_2'),
                description_3=query_description.get('description_3'),
                description_4=query_description.get('description_4'),
                description_5=query_description.get('description_5')
            )
        else:
            raise ValueError("Either query_text or query_description must be provided")

        # Generate query embedding
        query_embedding = self.generate_embedding(combined_query)

        # Search based on mode
        if self.use_database:
            results = self._search_database(query_embedding, top_k)
        else:
            results = self._search_memory(query_embedding, top_k)

        return results

    def _search_memory(self, query_embedding: np.ndarray, top_k: int) -> List[Dict]:
        """Search in-memory cases"""
        if not self.cases:
            logger.warning("No cases loaded in memory")
            return []

        # Calculate similarities
        similarities = cosine_similarity([query_embedding], self.embeddings_matrix)[0]

        # Get top-k indices
        top_indices = np.argsort(similarities)[::-1][:top_k]

        # Build results
        results = []
        for rank, idx in enumerate(top_indices, 1):
            results.append({
                'id': self.cases[idx]['id'],
                'description': self.cases[idx]['description'],
                'combined_text': self.cases[idx]['combined_text'],
                'similarity_score': float(similarities[idx]),
                'rank': rank
            })

        return results

    def _search_database(self, query_embedding: np.ndarray, top_k: int) -> List[Dict]:
        """Search using PostgreSQL database"""
        try:
            import psycopg2
            from psycopg2.extras import RealDictCursor

            # Connect to database
            conn = psycopg2.connect(**self.db_config)
            cur = conn.cursor(cursor_factory=RealDictCursor)

            # Get all complaints with embeddings
            cur.execute("""
                SELECT id, complaint_title, complaint_description,
                       w1h_summary, embedding, classification, status
                FROM complaints
                WHERE embedding IS NOT NULL
                AND status = 'processed'
            """)

            complaints = cur.fetchall()
            cur.close()
            conn.close()

            if not complaints:
                logger.warning("No complaints with embeddings found in database")
                return []

            logger.info(f"Found {len(complaints)} complaints with embeddings")

            # Calculate similarities
            similarities = []
            for complaint in complaints:
                complaint_embedding = np.array(complaint['embedding'])
                similarity = cosine_similarity([query_embedding], [complaint_embedding])[0][0]

                similarities.append({
                    'id': complaint['id'],
                    'complaint_title': complaint['complaint_title'],
                    'description': complaint['complaint_description'],
                    'w1h_summary': complaint['w1h_summary'],
                    'classification': complaint['classification'],
                    'similarity_score': float(similarity)
                })

            # Sort and get top-k
            similarities.sort(key=lambda x: x['similarity_score'], reverse=True)

            # Add rank
            for rank, result in enumerate(similarities[:top_k], 1):
                result['rank'] = rank

            return similarities[:top_k]

        except Exception as e:
            logger.error(f"Database search error: {e}")
            import traceback
            traceback.print_exc()
            return []

    def save(self, path: str = "case_search_engine.pkl"):
        """Save the search engine to file"""
        data = {
            'model_name': self.model_name,
            'cases': self.cases,
            'embeddings_matrix': self.embeddings_matrix
        }

        with open(path, 'wb') as f:
            pickle.dump(data, f)

        logger.info(f"✅ Search engine saved to {path}")

    def load(self, path: str = "case_search_engine.pkl"):
        """Load the search engine from file"""
        if not os.path.exists(path):
            raise FileNotFoundError(f"File not found: {path}")

        with open(path, 'rb') as f:
            data = pickle.load(f)

        self.model_name = data['model_name']
        self.cases = data['cases']
        self.embeddings_matrix = data['embeddings_matrix']

        # Load embedding model
        self.load_model()

        logger.info(f"✅ Search engine loaded from {path} ({len(self.cases)} cases)")


# Standalone usage example
if __name__ == "__main__":
    # Initialize search engine (in-memory mode)
    engine = CaseSearchEngine()

    # Example: Add some cases manually
    engine.add_case(
        case_id=1,
        description="Pegawai kerajaan menerima rasuah untuk meluluskan projek",
        description_5="Projek pembinaan bernilai RM 5 juta"
    )

    engine.add_case(
        case_id=2,
        description="Aduan tentang penyelewengan tender",
        description_5="Tender projek jalan raya tidak telus"
    )

    engine.add_case(
        case_id=3,
        description="Perkhidmatan pelanggan yang lemah",
        description_5="Respons lambat terhadap aduan awam"
    )

    # Search for similar cases
    results = engine.search(query_text="pegawai menerima wang haram untuk kelulusan tender")

    print("\n" + "="*60)
    print("🔍 Search Results:")
    print("="*60)
    for result in results:
        print(f"\nRank {result['rank']}: Case ID {result['id']}")
        print(f"Similarity: {result['similarity_score']:.4f}")
        print(f"Description: {result['description']}")

    # Save engine
    engine.save()
