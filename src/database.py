"""
Database configuration and connection management
"""
import os
from typing import Optional
import psycopg2
from psycopg2.extras import RealDictCursor
from psycopg2.pool import SimpleConnectionPool
from contextlib import contextmanager
from dotenv import load_dotenv

# Load environment variables
load_dotenv()


class Database:
    """PostgreSQL database connection manager"""

    def __init__(self):
        """Initialize database connection pool"""
        self.pool: Optional[SimpleConnectionPool] = None
        self._initialize_pool()

    def _initialize_pool(self):
        """Create connection pool from environment variables"""
        # Get database credentials
        db_host = os.getenv("DB_HOST", "localhost")
        db_port = os.getenv("DB_PORT", "5432")
        db_name = os.getenv("DB_NAME", "sprm_db")
        db_user = os.getenv("DB_USER", "postgres")
        db_password = os.getenv("DB_PASSWORD", "postgres")

        print(f"🔌 Connecting to PostgreSQL at {db_host}:{db_port}/{db_name} as {db_user}")

        try:
            self.pool = SimpleConnectionPool(
                minconn=1,
                maxconn=10,
                host=db_host,
                port=db_port,
                database=db_name,
                user=db_user,
                password=db_password
            )
            print("✅ Database connection pool initialized successfully")
        except psycopg2.OperationalError as e:
            print(f"❌ Database connection failed: {e}")
            print(f"   Host: {db_host}, Port: {db_port}, Database: {db_name}, User: {db_user}")
            print("💡 Make sure PostgreSQL is running and credentials are correct")
            self.pool = None
        except Exception as e:
            print(f"❌ Unexpected database error: {e}")
            self.pool = None

    @contextmanager
    def get_connection(self):
        """Get database connection from pool"""
        if self.pool is None:
            raise Exception("Database pool not initialized")

        conn = self.pool.getconn()
        try:
            yield conn
            conn.commit()
        except Exception as e:
            conn.rollback()
            raise e
        finally:
            self.pool.putconn(conn)

    @contextmanager
    def get_cursor(self, cursor_factory=RealDictCursor):
        """Get database cursor with automatic connection management"""
        with self.get_connection() as conn:
            cursor = conn.cursor(cursor_factory=cursor_factory)
            try:
                yield cursor
            finally:
                cursor.close()

    def execute_query(self, query: str, params: tuple = None):
        """Execute a query and return results"""
        with self.get_cursor() as cursor:
            cursor.execute(query, params)
            try:
                return cursor.fetchall()
            except psycopg2.ProgrammingError:
                # No results to fetch (INSERT, UPDATE, DELETE)
                return None

    def execute_insert(self, query: str, params: tuple = None):
        """Execute INSERT and return inserted ID"""
        with self.get_cursor() as cursor:
            cursor.execute(query, params)
            return cursor.fetchone()['id']

    def create_tables(self):
        """Create necessary database tables"""
        create_complaints_table = """
        CREATE TABLE IF NOT EXISTS complaints (
            id SERIAL PRIMARY KEY,

            -- Complainant Information
            full_name VARCHAR(255),
            ic_number VARCHAR(20),
            phone_number VARCHAR(20) NOT NULL,
            email VARCHAR(255),

            -- Complaint Details
            complaint_title VARCHAR(500) NOT NULL,
            category VARCHAR(100) NOT NULL,
            urgency_level VARCHAR(50) DEFAULT 'Sederhana',
            complaint_description TEXT NOT NULL,

            -- VLLM Processing Results
            extracted_data JSONB,
            w1h_summary TEXT,                  -- Full combined summary (for backward compatibility)

            -- 5W1H Structured Fields
            w1h_what TEXT,                     -- What happened (Apa)
            w1h_who TEXT,                      -- Who was involved (Siapa)
            w1h_when TEXT,                     -- When it happened (Bila)
            w1h_where TEXT,                    -- Where it happened (Di mana)
            w1h_why TEXT,                      -- Why it happened (Mengapa)
            w1h_how TEXT,                      -- How it happened (Bagaimana)

            -- AI-Generated Categories
            sector VARCHAR(100),               -- Government sector involved
            akta VARCHAR(200),                 -- Relevant legislation/act

            -- Embeddings for Similarity Search
            embedding FLOAT[],                 -- 384-dimensional embedding vector (all-MiniLM-L6-v2)

            -- Processing Status
            status VARCHAR(50) DEFAULT 'pending',
            classification VARCHAR(50),
            classification_confidence FLOAT,

            -- Timestamps
            submitted_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            processed_at TIMESTAMP,

            -- Metadata
            has_documents BOOLEAN DEFAULT FALSE,
            document_count INTEGER DEFAULT 0
        );
        """

        create_documents_table = """
        CREATE TABLE IF NOT EXISTS complaint_documents (
            id SERIAL PRIMARY KEY,
            complaint_id INTEGER REFERENCES complaints(id) ON DELETE CASCADE,
            filename VARCHAR(255) NOT NULL,
            original_filename VARCHAR(255) NOT NULL,
            file_path VARCHAR(500) NOT NULL,
            file_size INTEGER,
            file_type VARCHAR(50),
            uploaded_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        );
        """

        create_cases_table = """
        CREATE TABLE IF NOT EXISTS cases (
            id SERIAL PRIMARY KEY,
            case_number VARCHAR(50) UNIQUE NOT NULL,
            case_title VARCHAR(500) NOT NULL,
            case_description TEXT,

            -- Auto-generated metadata
            primary_complaint_id INTEGER REFERENCES complaints(id) ON DELETE SET NULL,
            common_keywords TEXT[],
            common_entities JSONB,

            -- Status and classification
            status VARCHAR(50) DEFAULT 'open',  -- open, investigating, closed
            priority VARCHAR(50) DEFAULT 'medium',  -- low, medium, high, critical
            classification VARCHAR(50),  -- CRIS or NFA (inherited from complaints)

            -- Timestamps
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            closed_at TIMESTAMP,

            -- Metadata
            complaint_count INTEGER DEFAULT 0,
            auto_grouped BOOLEAN DEFAULT TRUE
        );
        """

        create_case_complaints_table = """
        CREATE TABLE IF NOT EXISTS case_complaints (
            id SERIAL PRIMARY KEY,
            case_id INTEGER REFERENCES cases(id) ON DELETE CASCADE,
            complaint_id INTEGER REFERENCES complaints(id) ON DELETE CASCADE,
            similarity_score FLOAT,
            added_by VARCHAR(50) DEFAULT 'system',  -- 'system' or 'user'
            added_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,

            UNIQUE(case_id, complaint_id)
        );
        """

        create_similar_cases_table = """
        CREATE TABLE IF NOT EXISTS similar_cases (
            id SERIAL PRIMARY KEY,
            complaint_id INTEGER REFERENCES complaints(id) ON DELETE CASCADE,
            similar_complaint_id INTEGER,
            similarity_score FLOAT,
            rank INTEGER,
            found_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        );
        """

        create_indexes = """
        CREATE INDEX IF NOT EXISTS idx_complaints_status ON complaints(status);
        CREATE INDEX IF NOT EXISTS idx_complaints_submitted_at ON complaints(submitted_at);
        CREATE INDEX IF NOT EXISTS idx_complaints_category ON complaints(category);
        CREATE INDEX IF NOT EXISTS idx_documents_complaint_id ON complaint_documents(complaint_id);
        CREATE INDEX IF NOT EXISTS idx_similar_cases_complaint_id ON similar_cases(complaint_id);
        CREATE INDEX IF NOT EXISTS idx_cases_status ON cases(status);
        CREATE INDEX IF NOT EXISTS idx_cases_created_at ON cases(created_at);
        CREATE INDEX IF NOT EXISTS idx_case_complaints_case_id ON case_complaints(case_id);
        CREATE INDEX IF NOT EXISTS idx_case_complaints_complaint_id ON case_complaints(complaint_id);
        """

        # Migration: Add missing columns to existing tables
        add_missing_columns = """
        DO $$
        BEGIN
            -- Add extracted_data if not exists
            IF NOT EXISTS (
                SELECT 1 FROM information_schema.columns
                WHERE table_name = 'complaints' AND column_name = 'extracted_data'
            ) THEN
                ALTER TABLE complaints ADD COLUMN extracted_data JSONB;
            END IF;

            -- Add w1h_summary if not exists
            IF NOT EXISTS (
                SELECT 1 FROM information_schema.columns
                WHERE table_name = 'complaints' AND column_name = 'w1h_summary'
            ) THEN
                ALTER TABLE complaints ADD COLUMN w1h_summary TEXT;
            END IF;

            -- Add 5W1H structured columns
            IF NOT EXISTS (
                SELECT 1 FROM information_schema.columns
                WHERE table_name = 'complaints' AND column_name = 'w1h_what'
            ) THEN
                ALTER TABLE complaints ADD COLUMN w1h_what TEXT;
            END IF;

            IF NOT EXISTS (
                SELECT 1 FROM information_schema.columns
                WHERE table_name = 'complaints' AND column_name = 'w1h_who'
            ) THEN
                ALTER TABLE complaints ADD COLUMN w1h_who TEXT;
            END IF;

            IF NOT EXISTS (
                SELECT 1 FROM information_schema.columns
                WHERE table_name = 'complaints' AND column_name = 'w1h_when'
            ) THEN
                ALTER TABLE complaints ADD COLUMN w1h_when TEXT;
            END IF;

            IF NOT EXISTS (
                SELECT 1 FROM information_schema.columns
                WHERE table_name = 'complaints' AND column_name = 'w1h_where'
            ) THEN
                ALTER TABLE complaints ADD COLUMN w1h_where TEXT;
            END IF;

            IF NOT EXISTS (
                SELECT 1 FROM information_schema.columns
                WHERE table_name = 'complaints' AND column_name = 'w1h_why'
            ) THEN
                ALTER TABLE complaints ADD COLUMN w1h_why TEXT;
            END IF;

            IF NOT EXISTS (
                SELECT 1 FROM information_schema.columns
                WHERE table_name = 'complaints' AND column_name = 'w1h_how'
            ) THEN
                ALTER TABLE complaints ADD COLUMN w1h_how TEXT;
            END IF;

            -- Add sector column
            IF NOT EXISTS (
                SELECT 1 FROM information_schema.columns
                WHERE table_name = 'complaints' AND column_name = 'sector'
            ) THEN
                ALTER TABLE complaints ADD COLUMN sector VARCHAR(100);
            END IF;

            -- Add akta column
            IF NOT EXISTS (
                SELECT 1 FROM information_schema.columns
                WHERE table_name = 'complaints' AND column_name = 'akta'
            ) THEN
                ALTER TABLE complaints ADD COLUMN akta VARCHAR(200);
            END IF;

            -- Add embedding column
            IF NOT EXISTS (
                SELECT 1 FROM information_schema.columns
                WHERE table_name = 'complaints' AND column_name = 'embedding'
            ) THEN
                ALTER TABLE complaints ADD COLUMN embedding FLOAT[];
            END IF;
        END $$;
        """

        try:
            with self.get_cursor() as cursor:
                cursor.execute(create_complaints_table)
                cursor.execute(create_documents_table)
                cursor.execute(create_cases_table)
                cursor.execute(create_case_complaints_table)
                cursor.execute(create_similar_cases_table)
                cursor.execute(create_indexes)
                cursor.execute(add_missing_columns)
            print("✅ Database tables created/updated successfully")
        except Exception as e:
            print(f"❌ Error creating tables: {e}")
            raise

    def close(self):
        """Close all connections in the pool"""
        if self.pool:
            self.pool.closeall()
            print("✅ Database connections closed")


# Global database instance
db = Database()
