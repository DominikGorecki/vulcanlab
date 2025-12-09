-- Migration: Add tsvector column to chunks and retrieved_context to queries
-- Run this migration on existing databases

-- Add tsvector column to chunks table for full-text search
ALTER TABLE chunks ADD COLUMN IF NOT EXISTS content_tsvector tsvector;

-- Create GIN index for full-text search
CREATE INDEX IF NOT EXISTS ix_chunks_content_tsvector_gin
    ON chunks USING gin (content_tsvector);

-- Create trigger function to auto-update tsvector on insert/update
CREATE OR REPLACE FUNCTION chunks_content_tsvector_trigger()
RETURNS trigger AS $$
BEGIN
    NEW.content_tsvector := to_tsvector('english', COALESCE(NEW.content, ''));
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

-- Create trigger (drop first if exists to avoid duplicates)
DROP TRIGGER IF EXISTS tsvector_update ON chunks;
CREATE TRIGGER tsvector_update
    BEFORE INSERT OR UPDATE OF content ON chunks
    FOR EACH ROW
    EXECUTE FUNCTION chunks_content_tsvector_trigger();

-- Populate tsvector for existing data (batch update)
-- Run this in batches to avoid long locks on large tables
-- Batch size of 1000 rows at a time
DO $$
DECLARE
    batch_size INT := 1000;
    rows_updated INT;
BEGIN
    LOOP
        UPDATE chunks
        SET content_tsvector = to_tsvector('english', COALESCE(content, ''))
        WHERE id IN (
            SELECT id FROM chunks
            WHERE content_tsvector IS NULL
            LIMIT batch_size
        );

        GET DIAGNOSTICS rows_updated = ROW_COUNT;

        -- Commit each batch (implicit in DO block)
        RAISE NOTICE 'Updated % rows', rows_updated;

        EXIT WHEN rows_updated = 0;
    END LOOP;
END $$;

-- Add retrieved_context column to queries table
ALTER TABLE queries ADD COLUMN IF NOT EXISTS retrieved_context JSON;
