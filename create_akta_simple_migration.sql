-- Migration: Create akta_sections table (simplified - no vector)
-- Stores all akta sections for text-based search

CREATE TABLE IF NOT EXISTS akta_sections (
    id SERIAL PRIMARY KEY,
    section_code VARCHAR(50) NOT NULL UNIQUE,  -- e.g., "Seksyen 161", "Seksyen 48 AMLFPUAA"
    section_title TEXT NOT NULL,                -- e.g., "Mengambil suapan bersangkut perbuatan resmi"
    description TEXT,                            -- Detailed description for search
    category VARCHAR(100),                       -- e.g., "Rasuah", "Pemalsuan", "Wang Haram"
    act_name VARCHAR(200),                       -- e.g., "Kanun Keseksaan", "AMLFPUAA 2001"

    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Create index for category lookup
CREATE INDEX IF NOT EXISTS idx_akta_sections_category ON akta_sections(category);

-- Create text search index
CREATE INDEX IF NOT EXISTS idx_akta_sections_title ON akta_sections
USING gin(to_tsvector('simple', section_title || ' ' || COALESCE(description, '')));

COMMENT ON TABLE akta_sections IS 'Akta sections for AI classification';
