-- Migration: Change akta column from VARCHAR(200) to TEXT
-- Date: 2025-10-31
-- Purpose: Allow longer AKTA names that exceed 200 characters

-- Change akta column to TEXT (no length limit)
ALTER TABLE complaints
ALTER COLUMN akta TYPE TEXT;

COMMENT ON COLUMN complaints.akta IS 'AKTA classification (no length limit) - AI can generate longer act names';
