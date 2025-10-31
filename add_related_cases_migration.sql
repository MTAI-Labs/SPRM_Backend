-- Migration: Add related_cases support for tracking similar closed cases
-- This allows new complaints to reference previously closed similar cases

-- Add related_cases column to cases table
-- Stores array of case IDs that are similar but closed
ALTER TABLE cases ADD COLUMN IF NOT EXISTS related_cases JSONB DEFAULT '[]'::jsonb;

-- Add index for faster JSONB queries
CREATE INDEX IF NOT EXISTS idx_cases_related_cases ON cases USING gin (related_cases);

-- Add comment for documentation
COMMENT ON COLUMN cases.related_cases IS 'Array of related case references: [{"case_id": 123, "similarity_score": 0.85, "case_number": "CASE-2024-0015", "status": "closed", "detected_at": "2025-10-30T10:00:00"}]';

-- Example query to find cases with related closed cases:
-- SELECT * FROM cases WHERE jsonb_array_length(related_cases) > 0;
