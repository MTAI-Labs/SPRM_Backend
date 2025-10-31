-- Migration: Update complaint submission fields
-- Date: 2025-10-31
-- Purpose:
--   1. Make phone_number optional (was required)
--   2. Make category optional (remove NOT NULL)
--   3. Make urgency_level optional

-- Remove NOT NULL constraint from phone_number
ALTER TABLE complaints
ALTER COLUMN phone_number DROP NOT NULL;

-- Remove NOT NULL constraint from category (if exists)
ALTER TABLE complaints
ALTER COLUMN category DROP NOT NULL;

-- Category and urgency_level already allow NULL by default
-- Just update comments for clarity

COMMENT ON COLUMN complaints.full_name IS 'Complainant full name (optional - allows anonymous complaints)';
COMMENT ON COLUMN complaints.ic_number IS 'IC/Passport number (optional)';
COMMENT ON COLUMN complaints.phone_number IS 'Contact phone number (optional)';
COMMENT ON COLUMN complaints.email IS 'Email address (optional)';
COMMENT ON COLUMN complaints.category IS 'Complaint category (optional - deprecated)';
COMMENT ON COLUMN complaints.urgency_level IS 'Urgency level (optional - deprecated)';

-- Note: category and urgency_level columns kept for backward compatibility
-- but are no longer used in new submissions
