-- Migration: Add officer review fields to complaints table
-- Date: 2025-10-31
-- Purpose: Allow officers to manually review and update complaint status

-- Add officer review columns
ALTER TABLE complaints
ADD COLUMN IF NOT EXISTS officer_status VARCHAR(50),
ADD COLUMN IF NOT EXISTS officer_remarks TEXT,
ADD COLUMN IF NOT EXISTS reviewed_by VARCHAR(100),
ADD COLUMN IF NOT EXISTS reviewed_at TIMESTAMP;

-- Add index for officer_status
CREATE INDEX IF NOT EXISTS idx_complaints_officer_status ON complaints(officer_status);

-- Comment on new columns
COMMENT ON COLUMN complaints.officer_status IS 'Officer decision: pending_review, nfa, escalated, investigating, closed';
COMMENT ON COLUMN complaints.officer_remarks IS 'Officer notes and remarks about the complaint';
COMMENT ON COLUMN complaints.reviewed_by IS 'Officer username/ID who reviewed the complaint';
COMMENT ON COLUMN complaints.reviewed_at IS 'Timestamp when officer reviewed the complaint';

-- Update existing complaints to pending_review if processed
UPDATE complaints
SET officer_status = 'pending_review'
WHERE status = 'processed' AND officer_status IS NULL;
