-- Migration: Remove common_keywords column from cases table
-- Keywords were not used for similarity search, 5W1H generation, or classification
-- They only generated noise (e.g., "1111", "2222") without meaningful contribution

-- Drop the common_keywords column
ALTER TABLE cases DROP COLUMN IF EXISTS common_keywords;

-- Drop common_entities column as well (replaced by extracted_data in complaints table)
ALTER TABLE cases DROP COLUMN IF EXISTS common_entities;

-- Case titles are now:
-- - Single complaint: Uses complaint title
-- - Multiple complaints: "Kes: X Aduan Berkaitan"
