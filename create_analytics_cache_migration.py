"""
Create analytics cache table migration
"""
import os
import psycopg2
from psycopg2.extras import RealDictCursor
from dotenv import load_dotenv

# Load environment
load_dotenv()

def run_migration():
    """Create analytics_cache table"""

    # Database connection parameters
    db_config = {
        'host': os.getenv('DB_HOST', 'localhost'),
        'port': int(os.getenv('DB_PORT', 5432)),
        'database': os.getenv('DB_NAME', 'sprm_db'),
        'user': os.getenv('DB_USER', 'postgres'),
        'password': os.getenv('DB_PASSWORD', 'postgres')
    }

    migration_sql = """
    -- Create analytics cache table
    CREATE TABLE IF NOT EXISTS analytics_cache (
        id SERIAL PRIMARY KEY,
        cache_key VARCHAR(255) UNIQUE NOT NULL,
        cache_data JSONB NOT NULL,
        period_days INT,
        computed_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        expires_at TIMESTAMP,
        complaint_count INT,
        CONSTRAINT valid_cache_key CHECK (cache_key ~ '^[a-z0-9_]+$')
    );

    -- Indexes
    CREATE INDEX IF NOT EXISTS idx_analytics_cache_key ON analytics_cache(cache_key);
    CREATE INDEX IF NOT EXISTS idx_analytics_cache_expires ON analytics_cache(expires_at);

    -- Cleanup function
    CREATE OR REPLACE FUNCTION cleanup_expired_analytics_cache()
    RETURNS INTEGER AS $$
    DECLARE
        deleted_count INTEGER;
    BEGIN
        DELETE FROM analytics_cache
        WHERE expires_at < CURRENT_TIMESTAMP;
        GET DIAGNOSTICS deleted_count = ROW_COUNT;
        RETURN deleted_count;
    END;
    $$ LANGUAGE plpgsql;
    """

    try:
        print("Running migration: Create analytics_cache table...")

        # Connect to database
        conn = psycopg2.connect(**db_config)
        conn.autocommit = True

        with conn.cursor(cursor_factory=RealDictCursor) as cursor:
            cursor.execute(migration_sql)

        print("SUCCESS: Migration completed!")
        print("- Created 'analytics_cache' table")
        print("- Created indexes for fast lookups")
        print("- Created cleanup function")

        # Verify the table was created
        with conn.cursor(cursor_factory=RealDictCursor) as cursor:
            cursor.execute("""
                SELECT table_name
                FROM information_schema.tables
                WHERE table_name = 'analytics_cache'
            """)
            result = cursor.fetchone()

            if result:
                print(f"- Table verified: {result['table_name']}")
            else:
                print("WARNING: Could not verify table was created")

        conn.close()
        return True

    except Exception as e:
        print(f"ERROR: Migration failed: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    import sys
    success = run_migration()
    sys.exit(0 if success else 1)
