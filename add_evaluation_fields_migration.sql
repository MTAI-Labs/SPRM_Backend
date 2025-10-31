-- Migration: Add evaluation fields for officer review
-- These fields are filled by officers after reviewing AI-generated data

-- Add evaluation fields to complaints table
ALTER TABLE complaints
ADD COLUMN IF NOT EXISTS type_of_information VARCHAR(50),     -- Intelligence, Complaint, Report, etc.
ADD COLUMN IF NOT EXISTS source_type VARCHAR(50),              -- Public, Agency, Media, etc.
ADD COLUMN IF NOT EXISTS sub_sector VARCHAR(200),              -- Sub-category of main sector
ADD COLUMN IF NOT EXISTS currency_type VARCHAR(10),            -- MYR, USD, SGD, etc.
ADD COLUMN IF NOT EXISTS property_value NUMERIC(15, 2),        -- Value in specified currency
ADD COLUMN IF NOT EXISTS cris_details_others TEXT,             -- Additional CRIS information
ADD COLUMN IF NOT EXISTS akta_sections TEXT[],                 -- Array of akta sections (can be multiple)
ADD COLUMN IF NOT EXISTS evaluated_at TIMESTAMP,               -- When officer completed evaluation
ADD COLUMN IF NOT EXISTS evaluated_by VARCHAR(100);            -- Officer username/ID who evaluated

-- Add index for evaluation status
CREATE INDEX IF NOT EXISTS idx_complaints_evaluated ON complaints(evaluated_at);

-- Add index for type of information
CREATE INDEX IF NOT EXISTS idx_complaints_type_info ON complaints(type_of_information);

COMMENT ON COLUMN complaints.type_of_information IS 'Type of intelligence/complaint (e.g., Intelligence, Complaint, Report)';
COMMENT ON COLUMN complaints.source_type IS 'Source of complaint (e.g., Public, Government Agency, Media)';
COMMENT ON COLUMN complaints.sub_sector IS 'Detailed sub-category under main sector';
COMMENT ON COLUMN complaints.akta_sections IS 'Array of applicable akta sections (officers can select multiple)';
COMMENT ON COLUMN complaints.evaluated_at IS 'Timestamp when officer completed evaluation form';
COMMENT ON COLUMN complaints.evaluated_by IS 'Officer who evaluated and confirmed the data';
