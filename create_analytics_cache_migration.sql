-- Migration: Create analytics cache table
-- Date: 2025-10-31
-- Purpose: Cache analytics results for instant dashboard loading

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

-- Index for faster lookups
CREATE INDEX IF NOT EXISTS idx_analytics_cache_key ON analytics_cache(cache_key);
CREATE INDEX IF NOT EXISTS idx_analytics_cache_expires ON analytics_cache(expires_at);
CREATE INDEX IF NOT EXISTS idx_analytics_cache_period ON analytics_cache(period_days);

-- Comment
COMMENT ON TABLE analytics_cache IS 'Cache for analytics dashboard data - refreshed on complaint creation/update';
COMMENT ON COLUMN analytics_cache.cache_key IS 'Unique key like "dashboard_7d", "dashboard_30d", "patterns_30d"';
COMMENT ON COLUMN analytics_cache.cache_data IS 'Cached analytics results as JSON';
COMMENT ON COLUMN analytics_cache.period_days IS 'Time period analyzed (7, 30, 90 days)';
COMMENT ON COLUMN analytics_cache.complaint_count IS 'Number of complaints analyzed';
COMMENT ON COLUMN analytics_cache.computed_at IS 'When analytics were last computed';
COMMENT ON COLUMN analytics_cache.expires_at IS 'When cache expires (auto-refresh after this time)';
