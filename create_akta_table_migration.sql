-- Migration: Create akta_sections table for semantic search
-- Stores all akta sections with embeddings for fast similarity search

CREATE TABLE IF NOT EXISTS akta_sections (
    id SERIAL PRIMARY KEY,
    section_code VARCHAR(50) NOT NULL UNIQUE,  -- e.g., "Seksyen 161", "Seksyen 48 AMLFPUAA"
    section_title TEXT NOT NULL,                -- e.g., "Mengambil suapan bersangkut perbuatan resmi"
    description TEXT,                            -- Detailed description for search
    category VARCHAR(100),                       -- e.g., "Rasuah", "Pemalsuan", "Wang Haram"
    act_name VARCHAR(200),                       -- e.g., "Kanun Keseksaan", "AMLFPUAA 2001"

    -- Embedding for semantic search (384 dimensions for all-MiniLM-L6-v2)
    embedding vector(384),

    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Create index for fast vector similarity search
CREATE INDEX IF NOT EXISTS idx_akta_sections_embedding ON akta_sections
USING ivfflat (embedding vector_cosine_ops) WITH (lists = 100);

-- Create text search index for fallback
CREATE INDEX IF NOT EXISTS idx_akta_sections_title ON akta_sections
USING gin(to_tsvector('malay', section_title || ' ' || COALESCE(description, '')));

COMMENT ON TABLE akta_sections IS 'Akta sections with embeddings for semantic search';
COMMENT ON COLUMN akta_sections.embedding IS 'Sentence transformer embedding (384-dim) for similarity search';
