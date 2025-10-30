-- Add summary column to complaints table
-- This column will store AI-generated executive summaries (2-4 sentences)
-- based on form data, extracted data, and 5W1H analysis

ALTER TABLE complaints
ADD COLUMN IF NOT EXISTS summary TEXT;

COMMENT ON COLUMN complaints.summary IS 'AI-generated executive summary (2-4 sentences) based on complaint form, extracted data, and 5W1H analysis';
