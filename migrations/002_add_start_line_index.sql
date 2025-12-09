-- Migration: Add index on chunks.start_line
-- Run this script on existing databases to add the start_line index
-- This is non-destructive

-- Create index on start_line for faster lookups
CREATE INDEX IF NOT EXISTS ix_chunks_start_line ON chunks(start_line);

-- Verify index was created
SELECT 'start_line index created successfully' AS status
WHERE EXISTS (
    SELECT 1 FROM pg_indexes
    WHERE tablename = 'chunks' AND indexname = 'ix_chunks_start_line'
);
