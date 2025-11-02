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
                minconn=5,
                maxconn=50,
                host=db_host,
                port=db_port,
                database=db_name,
                user=db_user,
                password=db_password
            )
            print("✅ Database connection pool initialized successfully (min=5, max=50)")
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
            sub_sector VARCHAR(100),           -- Sub-sector within sector
            akta TEXT,                         -- Relevant legislation/act (can be long)
            summary TEXT,                      -- Executive summary of complaint

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

            -- Related cases tracking
            related_cases JSONB DEFAULT '[]'::jsonb,

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

        create_analytics_entities_table = """
        CREATE TABLE IF NOT EXISTS analytics_entities (
            id SERIAL PRIMARY KEY,
            entity_type VARCHAR(50) NOT NULL,
            entity_value TEXT NOT NULL,
            count INTEGER DEFAULT 1,
            last_updated TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            UNIQUE(entity_type, entity_value)
        );
        """

        create_analytics_sectors_table = """
        CREATE TABLE IF NOT EXISTS analytics_sectors (
            id SERIAL PRIMARY KEY,
            sector VARCHAR(100) NOT NULL,
            complaint_count INTEGER DEFAULT 1,
            yes_count INTEGER DEFAULT 0,
            no_count INTEGER DEFAULT 0,
            last_updated TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            UNIQUE(sector)
        );
        """

        create_analytics_patterns_table = """
        CREATE TABLE IF NOT EXISTS analytics_patterns (
            id SERIAL PRIMARY KEY,
            keyword1 VARCHAR(100) NOT NULL,
            keyword2 VARCHAR(100) NOT NULL,
            count INTEGER DEFAULT 1,
            last_updated TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            UNIQUE(keyword1, keyword2)
        );
        """

        create_analytics_summary_table = """
        CREATE TABLE IF NOT EXISTS analytics_summary (
            id INTEGER PRIMARY KEY DEFAULT 1,
            total_complaints INTEGER DEFAULT 0,
            yes_classification_count INTEGER DEFAULT 0,
            no_classification_count INTEGER DEFAULT 0,
            pending_review_count INTEGER DEFAULT 0,
            nfa_count INTEGER DEFAULT 0,
            escalated_count INTEGER DEFAULT 0,
            total_cases INTEGER DEFAULT 0,
            last_updated TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            CONSTRAINT single_row CHECK (id = 1)
        );
        """

        initialize_analytics_summary = """
        INSERT INTO analytics_summary (id) VALUES (1)
        ON CONFLICT (id) DO NOTHING;
        """

        create_akta_sections_table = """
        CREATE TABLE IF NOT EXISTS akta_sections (
            id SERIAL PRIMARY KEY,
            section_code VARCHAR(50) NOT NULL UNIQUE,
            section_title TEXT NOT NULL,
            description TEXT,
            category VARCHAR(100),
            act_name VARCHAR(200),
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        );
        """

        create_generated_letters_table = """
        CREATE TABLE IF NOT EXISTS generated_letters (
            id SERIAL PRIMARY KEY,
            complaint_id INTEGER REFERENCES complaints(id) ON DELETE CASCADE,
            letter_type VARCHAR(50) NOT NULL,
            letter_content TEXT NOT NULL,
            generated_by VARCHAR(100) NOT NULL,
            generated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            fields JSONB,
            file_path VARCHAR(255)
        );
        """

        create_analytics_cache_table = """
        CREATE TABLE IF NOT EXISTS analytics_cache (
            id SERIAL PRIMARY KEY,
            cache_key VARCHAR(100) UNIQUE NOT NULL,
            cache_data JSONB NOT NULL,
            period_days INTEGER,
            complaint_count INTEGER DEFAULT 0,
            computed_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            expires_at TIMESTAMP,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        );
        """

        create_audit_logs_table = """
        CREATE TABLE IF NOT EXISTS audit_logs (
            id SERIAL PRIMARY KEY,

            -- Who (User Context)
            user_id VARCHAR(100),
            user_role VARCHAR(50),
            ip_address INET,
            user_agent TEXT,

            -- What (Action Details)
            action VARCHAR(100) NOT NULL,
            entity_type VARCHAR(50) NOT NULL,
            entity_id INTEGER,

            -- Context (Additional Info)
            description TEXT,
            changes JSONB,
            metadata JSONB,

            -- When
            timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,

            -- Request Context
            endpoint VARCHAR(255),
            http_method VARCHAR(10),
            status_code INTEGER,

            -- Outcome
            success BOOLEAN DEFAULT TRUE,
            error_message TEXT
        );
        """

        create_indexes = """
        CREATE INDEX IF NOT EXISTS idx_complaints_status ON complaints(status);
        CREATE INDEX IF NOT EXISTS idx_complaints_officer_status ON complaints(officer_status);
        CREATE INDEX IF NOT EXISTS idx_complaints_submitted_at ON complaints(submitted_at);
        CREATE INDEX IF NOT EXISTS idx_complaints_category ON complaints(category);
        CREATE INDEX IF NOT EXISTS idx_documents_complaint_id ON complaint_documents(complaint_id);
        CREATE INDEX IF NOT EXISTS idx_similar_cases_complaint_id ON similar_cases(complaint_id);
        CREATE INDEX IF NOT EXISTS idx_cases_status ON cases(status);
        CREATE INDEX IF NOT EXISTS idx_cases_created_at ON cases(created_at);
        CREATE INDEX IF NOT EXISTS idx_case_complaints_case_id ON case_complaints(case_id);
        CREATE INDEX IF NOT EXISTS idx_case_complaints_complaint_id ON case_complaints(complaint_id);
        CREATE INDEX IF NOT EXISTS idx_analytics_entities_type ON analytics_entities(entity_type);
        CREATE INDEX IF NOT EXISTS idx_analytics_entities_count ON analytics_entities(count DESC);
        CREATE INDEX IF NOT EXISTS idx_analytics_sectors_count ON analytics_sectors(complaint_count DESC);
        CREATE INDEX IF NOT EXISTS idx_analytics_patterns_count ON analytics_patterns(count DESC);
        CREATE INDEX IF NOT EXISTS idx_akta_sections_category ON akta_sections(category);
        CREATE INDEX IF NOT EXISTS idx_akta_sections_title ON akta_sections USING gin(to_tsvector('simple', section_title || ' ' || COALESCE(description, '')));
        CREATE INDEX IF NOT EXISTS idx_cases_related_cases ON cases USING gin(related_cases);
        CREATE INDEX IF NOT EXISTS idx_generated_letters_complaint_id ON generated_letters(complaint_id);
        CREATE INDEX IF NOT EXISTS idx_generated_letters_generated_at ON generated_letters(generated_at DESC);
        CREATE INDEX IF NOT EXISTS idx_analytics_cache_key ON analytics_cache(cache_key);
        CREATE INDEX IF NOT EXISTS idx_analytics_cache_expires ON analytics_cache(expires_at);
        CREATE INDEX IF NOT EXISTS idx_audit_logs_user_id ON audit_logs(user_id);
        CREATE INDEX IF NOT EXISTS idx_audit_logs_action ON audit_logs(action);
        CREATE INDEX IF NOT EXISTS idx_audit_logs_entity ON audit_logs(entity_type, entity_id);
        CREATE INDEX IF NOT EXISTS idx_audit_logs_timestamp ON audit_logs(timestamp DESC);
        CREATE INDEX IF NOT EXISTS idx_audit_logs_ip_address ON audit_logs(ip_address);
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
                ALTER TABLE complaints ADD COLUMN akta TEXT;
            END IF;

            -- Change akta column type to TEXT if it's VARCHAR
            BEGIN
                ALTER TABLE complaints ALTER COLUMN akta TYPE TEXT;
            EXCEPTION
                WHEN others THEN NULL;
            END;

            -- Add sub_sector column
            IF NOT EXISTS (
                SELECT 1 FROM information_schema.columns
                WHERE table_name = 'complaints' AND column_name = 'sub_sector'
            ) THEN
                ALTER TABLE complaints ADD COLUMN sub_sector VARCHAR(100);
            END IF;

            -- Add summary column
            IF NOT EXISTS (
                SELECT 1 FROM information_schema.columns
                WHERE table_name = 'complaints' AND column_name = 'summary'
            ) THEN
                ALTER TABLE complaints ADD COLUMN summary TEXT;
            END IF;

            -- Add embedding column
            IF NOT EXISTS (
                SELECT 1 FROM information_schema.columns
                WHERE table_name = 'complaints' AND column_name = 'embedding'
            ) THEN
                ALTER TABLE complaints ADD COLUMN embedding FLOAT[];
            END IF;

            -- Add officer review columns
            IF NOT EXISTS (
                SELECT 1 FROM information_schema.columns
                WHERE table_name = 'complaints' AND column_name = 'officer_status'
            ) THEN
                ALTER TABLE complaints ADD COLUMN officer_status VARCHAR(50);
            END IF;

            IF NOT EXISTS (
                SELECT 1 FROM information_schema.columns
                WHERE table_name = 'complaints' AND column_name = 'officer_remarks'
            ) THEN
                ALTER TABLE complaints ADD COLUMN officer_remarks TEXT;
            END IF;

            IF NOT EXISTS (
                SELECT 1 FROM information_schema.columns
                WHERE table_name = 'complaints' AND column_name = 'reviewed_by'
            ) THEN
                ALTER TABLE complaints ADD COLUMN reviewed_by VARCHAR(100);
            END IF;

            IF NOT EXISTS (
                SELECT 1 FROM information_schema.columns
                WHERE table_name = 'complaints' AND column_name = 'reviewed_at'
            ) THEN
                ALTER TABLE complaints ADD COLUMN reviewed_at TIMESTAMP;
            END IF;

            -- Add related_cases column to cases table
            IF NOT EXISTS (
                SELECT 1 FROM information_schema.columns
                WHERE table_name = 'cases' AND column_name = 'related_cases'
            ) THEN
                ALTER TABLE cases ADD COLUMN related_cases JSONB DEFAULT '[]'::jsonb;
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
                cursor.execute(create_analytics_entities_table)
                cursor.execute(create_analytics_sectors_table)
                cursor.execute(create_analytics_patterns_table)
                cursor.execute(create_analytics_summary_table)
                cursor.execute(initialize_analytics_summary)
                cursor.execute(create_akta_sections_table)
                cursor.execute(create_generated_letters_table)
                cursor.execute(create_analytics_cache_table)
                cursor.execute(create_audit_logs_table)
                cursor.execute(add_missing_columns)
                cursor.execute(create_indexes)
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
