-- Migration 019: Add sentence_count column to chunks table
-- This migration adds a sentence count field to enable sentence-based filtering in RAG retrieval
-- NOTE: This migration should be run as the application user to ensure proper ownership

-- Add sentence_count column to chunks table
ALTER TABLE chunks ADD COLUMN IF NOT EXISTS sentence_count INTEGER NULL;

-- Create index for efficient filtering on sentence_count
CREATE INDEX IF NOT EXISTS idx_chunks_sentence_count ON chunks(sentence_count);

-- Verify column was added
SELECT 'sentence_count column and index created successfully' AS status
WHERE EXISTS (
    SELECT 1 FROM information_schema.columns
    WHERE table_name = 'chunks' AND column_name = 'sentence_count'
);

-- ROLLBACK INSTRUCTIONS (run manually if needed):
-- DROP INDEX IF EXISTS idx_chunks_sentence_count;
-- ALTER TABLE chunks DROP COLUMN IF EXISTS sentence_count;
