-- Create analytics cache table to store pre-computed analytics
-- This avoids recalculating analytics on every frontend request

CREATE TABLE IF NOT EXISTS analytics_cache (
    id SERIAL PRIMARY KEY,
    cache_key VARCHAR(255) UNIQUE NOT NULL,  -- e.g., 'dashboard_30d', 'patterns_7d'
    cache_data JSONB NOT NULL,               -- The computed analytics data
    period_days INT,                         -- Time period analyzed (7, 30, 90, etc.)
    computed_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    expires_at TIMESTAMP,                    -- When this cache entry expires
    complaint_count INT,                     -- Number of complaints analyzed
    CONSTRAINT valid_cache_key CHECK (cache_key ~ '^[a-z0-9_]+$')
);

-- Index for fast lookups
CREATE INDEX idx_analytics_cache_key ON analytics_cache(cache_key);
CREATE INDEX idx_analytics_cache_expires ON analytics_cache(expires_at);

-- Comment
COMMENT ON TABLE analytics_cache IS 'Pre-computed analytics cache to improve dashboard performance';
COMMENT ON COLUMN analytics_cache.cache_key IS 'Unique identifier like dashboard_30d, patterns_7d, entities_90d';
COMMENT ON COLUMN analytics_cache.cache_data IS 'Full JSON response data for the analytics';
COMMENT ON COLUMN analytics_cache.expires_at IS 'Cache expiry timestamp - recompute when expired';

-- Create function to clean up expired cache entries
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

COMMENT ON FUNCTION cleanup_expired_analytics_cache() IS 'Delete expired cache entries, returns number of deleted rows';
