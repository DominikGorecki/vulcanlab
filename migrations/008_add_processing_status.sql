-- Migration 008: Add processing_status JSON column to works table
--
-- This column tracks the status of various processing operations (chunking, vectorization, etc.)
-- using a JSON structure for flexibility.

-- Add processing_status JSONB column (JSONB supports GIN indexing, JSON does not)
ALTER TABLE works ADD COLUMN IF NOT EXISTS processing_status JSONB;

-- Create GIN index on processing_status for efficient querying
-- GIN index allows querying JSONB properties
CREATE INDEX IF NOT EXISTS ix_works_processing_status_gin ON works USING gin (processing_status);

-- Grant permissions to app user
-- (Assuming psych_rag_app_user_test is the app user, adjust if needed)
GRANT SELECT, INSERT, UPDATE, DELETE ON works TO psych_rag_app_user_test;

