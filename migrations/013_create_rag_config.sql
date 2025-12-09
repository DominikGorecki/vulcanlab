-- Migration 013: Create rag_config table for RAG configuration presets
-- This table stores configuration presets for retrieval, consolidation, and augmentation parameters
-- NOTE: This migration should be run as the application user to ensure proper ownership

CREATE TABLE IF NOT EXISTS rag_config (
    id SERIAL PRIMARY KEY,
    preset_name VARCHAR(100) UNIQUE NOT NULL,
    is_default BOOLEAN NOT NULL DEFAULT FALSE,
    description TEXT,
    config JSONB NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Create indexes for efficient lookups
CREATE INDEX IF NOT EXISTS idx_rag_config_preset_name ON rag_config(preset_name);
CREATE INDEX IF NOT EXISTS idx_rag_config_is_default ON rag_config(is_default) WHERE is_default = TRUE;

-- Add trigger to update updated_at timestamp
CREATE OR REPLACE FUNCTION update_rag_config_updated_at()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = CURRENT_TIMESTAMP;
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

CREATE TRIGGER trigger_update_rag_config_updated_at
    BEFORE UPDATE ON rag_config
    FOR EACH ROW
    EXECUTE FUNCTION update_rag_config_updated_at();

-- Add trigger to enforce single default preset constraint
CREATE OR REPLACE FUNCTION ensure_single_default_rag_config()
RETURNS TRIGGER AS $$
BEGIN
    IF NEW.is_default = TRUE THEN
        UPDATE rag_config SET is_default = FALSE WHERE id != NEW.id;
    END IF;
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

CREATE TRIGGER trigger_ensure_single_default_rag_config
    AFTER INSERT OR UPDATE ON rag_config
    FOR EACH ROW
    WHEN (NEW.is_default = TRUE)
    EXECUTE FUNCTION ensure_single_default_rag_config();

-- Insert default preset with balanced settings
INSERT INTO rag_config (preset_name, is_default, description, config)
VALUES (
    'Default',
    TRUE,
    'Default RAG configuration with balanced settings for general-purpose queries',
    '{
        "retrieval": {
            "dense_limit": 19,
            "lexical_limit": 5,
            "rrf_k": 50,
            "top_k_rrf": 75,
            "top_n_final": 17,
            "entity_boost": 0.05,
            "min_word_count": 150,
            "min_char_count": 250,
            "min_content_length": 750,
            "enrich_lines_above": 0,
            "enrich_lines_below": 13,
            "mmr_lambda": 0.7,
            "reranker_batch_size": 8,
            "reranker_max_length": 512
        },
        "consolidation": {
            "coverage_threshold": 0.5,
            "line_gap": 7,
            "min_content_length": 350,
            "enrich_from_md": true
        },
        "augmentation": {
            "top_n_contexts": 5
        }
    }'::JSONB
)
ON CONFLICT (preset_name) DO NOTHING;

-- Add comments to the table and columns
COMMENT ON TABLE rag_config IS 'RAG configuration presets for retrieval, consolidation, and augmentation parameters';
COMMENT ON COLUMN rag_config.preset_name IS 'Unique human-readable name for the preset';
COMMENT ON COLUMN rag_config.is_default IS 'Whether this preset is the default (only one can be true)';
COMMENT ON COLUMN rag_config.config IS 'JSONB configuration with retrieval, consolidation, and augmentation sections';

-- If this migration was run by an admin, transfer ownership to app user
-- Note: Replace 'psych_rag' with your actual app user if different
-- Uncomment and run if needed:
-- ALTER FUNCTION update_rag_config_updated_at() OWNER TO psych_rag;
-- ALTER FUNCTION ensure_single_default_rag_config() OWNER TO psych_rag;
-- ALTER SEQUENCE rag_config_id_seq OWNER TO psych_rag;
