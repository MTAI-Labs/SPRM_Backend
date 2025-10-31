-- Simple Analytics Tables
-- Pre-computed analytics stored in database for instant retrieval
-- Updated automatically when complaints are processed

-- 1. Entity counts (names, organizations, locations)
CREATE TABLE IF NOT EXISTS analytics_entities (
    id SERIAL PRIMARY KEY,
    entity_type VARCHAR(50) NOT NULL,  -- 'name', 'organization', 'location', 'amount'
    entity_value TEXT NOT NULL,
    count INTEGER DEFAULT 1,
    last_updated TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    UNIQUE(entity_type, entity_value)
);

CREATE INDEX IF NOT EXISTS idx_analytics_entities_type ON analytics_entities(entity_type);
CREATE INDEX IF NOT EXISTS idx_analytics_entities_count ON analytics_entities(count DESC);

-- 2. Sector/Category breakdown
CREATE TABLE IF NOT EXISTS analytics_sectors (
    id SERIAL PRIMARY KEY,
    sector VARCHAR(100) NOT NULL,
    complaint_count INTEGER DEFAULT 1,
    yes_count INTEGER DEFAULT 0,  -- Classification = YES
    no_count INTEGER DEFAULT 0,   -- Classification = NO
    last_updated TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    UNIQUE(sector)
);

CREATE INDEX IF NOT EXISTS idx_analytics_sectors_count ON analytics_sectors(complaint_count DESC);

-- 3. Keyword patterns (2-word combinations)
CREATE TABLE IF NOT EXISTS analytics_patterns (
    id SERIAL PRIMARY KEY,
    keyword1 VARCHAR(100) NOT NULL,
    keyword2 VARCHAR(100) NOT NULL,
    count INTEGER DEFAULT 1,
    last_updated TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    UNIQUE(keyword1, keyword2)
);

CREATE INDEX IF NOT EXISTS idx_analytics_patterns_count ON analytics_patterns(count DESC);

-- 4. Overall statistics (single row, updated on each complaint)
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

-- Insert initial row
INSERT INTO analytics_summary (id) VALUES (1)
ON CONFLICT (id) DO NOTHING;

COMMENT ON TABLE analytics_entities IS 'Pre-computed entity counts updated on each complaint';
COMMENT ON TABLE analytics_sectors IS 'Pre-computed sector statistics';
COMMENT ON TABLE analytics_patterns IS 'Pre-computed keyword pattern counts';
COMMENT ON TABLE analytics_summary IS 'Overall statistics (single row)';
