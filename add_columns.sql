-- Migration: Add extracted_data and w1h_summary columns
-- Run this if you get "column does not exist" error

-- Add extracted_data column (JSONB for storing AI extraction results)
ALTER TABLE complaints ADD COLUMN IF NOT EXISTS extracted_data JSONB;

-- Add w1h_summary column (TEXT for storing 5W1H summary)
ALTER TABLE complaints ADD COLUMN IF NOT EXISTS w1h_summary TEXT;

-- Verify columns were added
SELECT column_name, data_type
FROM information_schema.columns
WHERE table_name = 'complaints'
AND column_name IN ('extracted_data', 'w1h_summary');
