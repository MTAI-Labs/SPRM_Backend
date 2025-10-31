-- Simple Akta Sections Table (No pgvector required)
-- Just stores sections with categories for easy lookup

CREATE TABLE IF NOT EXISTS akta_sections (
    id SERIAL PRIMARY KEY,
    section_code VARCHAR(50) NOT NULL UNIQUE,  -- e.g., "Seksyen 161"
    section_title TEXT NOT NULL,                -- e.g., "Mengambil suapan bersangkut perbuatan resmi"
    category VARCHAR(100),                       -- e.g., "Rasuah & Suapan"
    act_name VARCHAR(200) DEFAULT 'Kanun Keseksaan',  -- e.g., "Kanun Keseksaan", "AMLFPUAA 2001"

    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Index for fast category lookup
CREATE INDEX IF NOT EXISTS idx_akta_sections_category ON akta_sections(category);

-- Index for text search on section code and title
CREATE INDEX IF NOT EXISTS idx_akta_sections_search ON akta_sections
USING gin(to_tsvector('simple', section_code || ' ' || section_title));

COMMENT ON TABLE akta_sections IS 'Akta sections organized by category (simple approach)';
