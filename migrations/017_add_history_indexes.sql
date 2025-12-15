-- Migration 017: Add indexes for simple conversion history queries
--
-- This migration adds two indexes to optimize history queries:
-- 1. General timestamp index for sorting all works by created_at
-- 2. Partial index for filtering simple conversion works with timestamp sorting
--
-- The partial index is more efficient than a full index because it only includes
-- works that have simple_conversion_mode in their processing_status JSON.

BEGIN;

-- Index 1: General timestamp index for sorting all works by creation date
-- Supports queries like: SELECT * FROM works ORDER BY created_at DESC LIMIT 20
CREATE INDEX IF NOT EXISTS ix_works_created_at
ON works (created_at DESC);

-- Index 2: Partial index for simple conversion works with timestamp sorting
-- Supports queries like:
--   SELECT * FROM works
--   WHERE processing_status ? 'simple_conversion_mode'
--   ORDER BY created_at DESC
-- The partial index only indexes rows where simple_conversion_mode exists in processing_status,
-- making it smaller and more efficient than a full composite index.
CREATE INDEX IF NOT EXISTS ix_works_simple_conversion_created_at
ON works (created_at DESC)
WHERE (processing_status ? 'simple_conversion_mode');

COMMIT;

-- Rollback script (for reference, not executed automatically):
-- BEGIN;
-- DROP INDEX IF EXISTS ix_works_simple_conversion_created_at;
-- DROP INDEX IF EXISTS ix_works_created_at;
-- COMMIT;
