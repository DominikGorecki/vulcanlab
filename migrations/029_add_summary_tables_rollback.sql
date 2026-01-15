-- Rollback: 029_add_summary_tables.sql
-- Description: Remove summary_nodes, work_summaries, summarize_settings tables and related objects
-- WARNING: This will delete all data in these tables

-- ============================================================================
-- 1. Drop triggers
-- ============================================================================
DROP TRIGGER IF EXISTS trigger_update_summarize_settings_updated_at ON summarize_settings;

-- ============================================================================
-- 2. Drop trigger functions
-- ============================================================================
DROP FUNCTION IF EXISTS update_summarize_settings_updated_at();

-- ============================================================================
-- 3. Drop indexes (will be dropped with tables, but explicit for clarity)
-- ============================================================================
DROP INDEX IF EXISTS idx_work_summaries_work_id;
DROP INDEX IF EXISTS idx_summary_nodes_work_id;
DROP INDEX IF EXISTS idx_summary_nodes_chunk_id;

-- ============================================================================
-- 4. Drop tables (in reverse order of creation to handle foreign keys)
-- ============================================================================
DROP TABLE IF EXISTS work_summaries CASCADE;
DROP TABLE IF EXISTS summary_nodes CASCADE;
DROP TABLE IF EXISTS summarize_settings CASCADE;

-- ============================================================================
-- 5. Verification queries
-- ============================================================================
SELECT 'work_summaries table dropped successfully' AS status
WHERE NOT EXISTS (
    SELECT 1 FROM information_schema.tables
    WHERE table_name = 'work_summaries'
);

SELECT 'summary_nodes table dropped successfully' AS status
WHERE NOT EXISTS (
    SELECT 1 FROM information_schema.tables
    WHERE table_name = 'summary_nodes'
);

SELECT 'summarize_settings table dropped successfully' AS status
WHERE NOT EXISTS (
    SELECT 1 FROM information_schema.tables
    WHERE table_name = 'summarize_settings'
);
