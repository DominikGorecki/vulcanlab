-- Migration: 029_add_summary_tables.sql
-- Description: Create summary_nodes, work_summaries, and summarize_settings tables
-- Implementation of Ticket: work-summarization.T02

-- ============================================================================
-- 1. Create summarize_settings table
-- ============================================================================
CREATE TABLE IF NOT EXISTS summarize_settings (
    id SERIAL PRIMARY KEY,
    h1_always_summarize BOOLEAN DEFAULT true,
    h2_top_percent INTEGER DEFAULT 100,
    h3_salience_threshold FLOAT DEFAULT 0.5,
    h4_salience_threshold FLOAT DEFAULT 0.7,
    definition_density_weight FLOAT DEFAULT 0.3,
    list_density_weight FLOAT DEFAULT 0.2,
    keyphrase_novelty_weight FLOAT DEFAULT 0.2,
    location_prior_weight FLOAT DEFAULT 0.15,
    heading_depth_weight FLOAT DEFAULT 0.15,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP NOT NULL,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP NOT NULL
);

COMMENT ON TABLE summarize_settings IS 'Configuration for salience-based summarization node selection';

-- ============================================================================
-- 2. Create summary_nodes table
-- ============================================================================
CREATE TABLE IF NOT EXISTS summary_nodes (
    id SERIAL PRIMARY KEY,
    chunk_id INTEGER NOT NULL REFERENCES chunks(id) ON DELETE CASCADE,
    work_id INTEGER NOT NULL REFERENCES works(id) ON DELETE CASCADE,
    gist TEXT NOT NULL,
    key_points JSONB NOT NULL DEFAULT '[]',
    definitions JSONB NOT NULL DEFAULT '[]',
    key_terms JSONB NOT NULL DEFAULT '[]',
    examples JSONB NOT NULL DEFAULT '[]',
    start_line INTEGER NOT NULL,
    end_line INTEGER NOT NULL,
    salience_score FLOAT NOT NULL,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP NOT NULL
);

-- Indexes for summary_nodes
CREATE INDEX IF NOT EXISTS idx_summary_nodes_work_id ON summary_nodes(work_id);
CREATE INDEX IF NOT EXISTS idx_summary_nodes_chunk_id ON summary_nodes(chunk_id);

COMMENT ON TABLE summary_nodes IS 'Granular summary data for individual heading-level chunks';

-- ============================================================================
-- 3. Create work_summaries table
-- ============================================================================
CREATE TABLE IF NOT EXISTS work_summaries (
    id SERIAL PRIMARY KEY,
    work_id INTEGER NOT NULL REFERENCES works(id) ON DELETE CASCADE,
    type VARCHAR(30) NOT NULL,
    content JSONB NOT NULL,
    line_references JSONB NOT NULL,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP NOT NULL,
    CONSTRAINT chk_work_summary_type CHECK (type IN ('abstract', 'outline', 'key_concepts', 'chapter_summaries')),
    CONSTRAINT unq_work_summary_work_type UNIQUE (work_id, type)
);

-- Index for work_summaries
CREATE INDEX IF NOT EXISTS idx_work_summaries_work_id ON work_summaries(work_id);

COMMENT ON TABLE work_summaries IS 'Derived high-level summaries for works (abstract, outline, etc.)';

-- ============================================================================
-- 4. Create trigger functions for auto-updating timestamps
-- ============================================================================
CREATE OR REPLACE FUNCTION update_summarize_settings_updated_at()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = CURRENT_TIMESTAMP;
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

-- ============================================================================
-- 5. Create triggers
-- ============================================================================
DROP TRIGGER IF EXISTS trigger_update_summarize_settings_updated_at ON summarize_settings;
CREATE TRIGGER trigger_update_summarize_settings_updated_at
    BEFORE UPDATE ON summarize_settings
    FOR EACH ROW
    EXECUTE FUNCTION update_summarize_settings_updated_at();

-- ============================================================================
-- 6. Verification queries
-- ============================================================================
SELECT 'summarize_settings table created successfully' AS status
WHERE EXISTS (
    SELECT 1 FROM information_schema.tables 
    WHERE table_name = 'summarize_settings'
);

SELECT 'summary_nodes table created successfully' AS status
WHERE EXISTS (
    SELECT 1 FROM information_schema.tables 
    WHERE table_name = 'summary_nodes'
);

SELECT 'work_summaries table created successfully' AS status
WHERE EXISTS (
    SELECT 1 FROM information_schema.tables 
    WHERE table_name = 'work_summaries'
);
