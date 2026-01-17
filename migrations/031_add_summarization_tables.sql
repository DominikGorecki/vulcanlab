-- Migration 031: Add summarization tables
-- This migration adds tables for storing summarization settings, intermediate chunks, and final results.
-- NOTE: This migration should be run as the application user to ensure proper ownership

-- 1. Create summarize_settings table
CREATE TABLE IF NOT EXISTS summarize_settings (
    id SERIAL PRIMARY KEY,
    min_heading_word_count INTEGER DEFAULT 500,
    max_total_heading_words INTEGER DEFAULT 2500,
    dense_top_k INTEGER DEFAULT 7,
    lexical_top_k INTEGER DEFAULT 7,
    rrf_k INTEGER DEFAULT 60,
    rrf_top_k INTEGER DEFAULT 7,
    mmr_lambda FLOAT DEFAULT 0.7,
    mmr_top_n INTEGER DEFAULT 5,
    max_llm_calls INTEGER DEFAULT 5,
    max_tokens_per_call INTEGER DEFAULT 15000,
    tokens_per_word FLOAT DEFAULT 0.75,
    h1_h2_min_chunks INTEGER DEFAULT 2,
    h3_min_chunks INTEGER DEFAULT 1,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

COMMENT ON TABLE summarize_settings IS 'Global configuration for the work summarization process';

-- 2. Create summary_chunks table
CREATE TABLE IF NOT EXISTS summary_chunks (
    id SERIAL PRIMARY KEY,
    work_id INTEGER NOT NULL REFERENCES works(id) ON DELETE CASCADE,
    heading_chunk_id INTEGER NOT NULL REFERENCES chunks(id) ON DELETE CASCADE,
    content_chunk_id INTEGER NOT NULL REFERENCES chunks(id) ON DELETE CASCADE,
    word_count INTEGER NOT NULL,
    dense_score FLOAT,
    lexical_score FLOAT,
    rrf_score FLOAT,
    mmr_score FLOAT,
    rank_position INTEGER NOT NULL,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

COMMENT ON TABLE summary_chunks IS 'Intermediate storage for chunks selected for summarization with their ranking scores';

-- 3. Create summary_results table
CREATE TABLE IF NOT EXISTS summary_results (
    id SERIAL PRIMARY KEY,
    work_id INTEGER NOT NULL REFERENCES works(id) ON DELETE CASCADE,
    chunk_id INTEGER UNIQUE NOT NULL REFERENCES chunks(id) ON DELETE CASCADE,
    summary_content TEXT NOT NULL,
    prompt_index INTEGER,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

COMMENT ON TABLE summary_results IS 'Final generated summaries for specific chunks (headings) within a work';

-- Indexes
CREATE INDEX IF NOT EXISTS idx_summary_chunks_work_id ON summary_chunks(work_id);
CREATE INDEX IF NOT EXISTS idx_summary_chunks_heading_chunk_id ON summary_chunks(heading_chunk_id);
CREATE INDEX IF NOT EXISTS idx_summary_chunks_heading_rank ON summary_chunks(heading_chunk_id, rank_position);
CREATE INDEX IF NOT EXISTS idx_summary_results_work_id ON summary_results(work_id);
CREATE INDEX IF NOT EXISTS idx_summary_results_chunk_id ON summary_results(chunk_id);

-- Trigger for summarize_settings.updated_at
CREATE OR REPLACE FUNCTION update_summarize_settings_updated_at()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = NOW();
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

DROP TRIGGER IF EXISTS trigger_update_summarize_settings_updated_at ON summarize_settings;
CREATE TRIGGER trigger_update_summarize_settings_updated_at
    BEFORE UPDATE ON summarize_settings
    FOR EACH ROW
    EXECUTE FUNCTION update_summarize_settings_updated_at();

-- Trigger for summary_results.updated_at
CREATE OR REPLACE FUNCTION update_summary_results_updated_at()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = NOW();
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

DROP TRIGGER IF EXISTS trigger_update_summary_results_updated_at ON summary_results;
CREATE TRIGGER trigger_update_summary_results_updated_at
    BEFORE UPDATE ON summary_results
    FOR EACH ROW
    EXECUTE FUNCTION update_summary_results_updated_at();

-- Verification queries
SELECT 'summarize_settings table exists' AS status
WHERE EXISTS (SELECT 1 FROM information_schema.tables WHERE table_name = 'summarize_settings');

SELECT 'summary_chunks table exists' AS status
WHERE EXISTS (SELECT 1 FROM information_schema.tables WHERE table_name = 'summary_chunks');

SELECT 'summary_results table exists' AS status
WHERE EXISTS (SELECT 1 FROM information_schema.tables WHERE table_name = 'summary_results');
