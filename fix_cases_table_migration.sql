-- Migration: Add related_cases column to cases table
-- Date: 2025-10-31
-- Purpose: Store related case IDs for auto-grouping feature

-- Add related_cases column (JSONB array of case IDs)
ALTER TABLE cases
ADD COLUMN IF NOT EXISTS related_cases JSONB DEFAULT '[]'::jsonb;

-- Add index for faster related_cases queries
CREATE INDEX IF NOT EXISTS idx_cases_related_cases ON cases USING gin(related_cases);

COMMENT ON COLUMN cases.related_cases IS 'Array of related case IDs (JSONB) for auto-grouping feature';
