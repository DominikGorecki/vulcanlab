-- Migration 025: Add model tracking for results
--
-- This migration creates the result_models table to track which LLM model
-- generated each result, and adds a model_id foreign key to the results table.

-- Create result_models table
CREATE TABLE IF NOT EXISTS result_models (
    id SERIAL PRIMARY KEY,
    name VARCHAR(200) UNIQUE NOT NULL,
    created_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT NOW()
);

-- Create index on name for unique constraint lookups
CREATE INDEX IF NOT EXISTS ix_result_models_name ON result_models(name);

-- Create trigger function for auto-updating updated_at timestamp
CREATE OR REPLACE FUNCTION update_result_models_updated_at()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = NOW();
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

-- Create trigger to call the function before UPDATE
CREATE TRIGGER trigger_update_result_models_updated_at
    BEFORE UPDATE ON result_models
    FOR EACH ROW
    EXECUTE FUNCTION update_result_models_updated_at();

-- Add model_id column to results table
ALTER TABLE results
ADD COLUMN IF NOT EXISTS model_id INTEGER NULL
REFERENCES result_models(id) ON DELETE SET NULL;

-- Create index on model_id for join performance
CREATE INDEX IF NOT EXISTS ix_results_model_id ON results(model_id);

-- Seed default "Unspecified" model
INSERT INTO result_models (name, created_at, updated_at)
VALUES ('Unspecified', NOW(), NOW())
ON CONFLICT (name) DO NOTHING;

-- Grant permissions to app user
GRANT SELECT, INSERT, UPDATE, DELETE ON result_models TO psych_rag_app_user_test;
GRANT USAGE, SELECT ON SEQUENCE result_models_id_seq TO psych_rag_app_user_test;

-- Add comments for documentation
COMMENT ON TABLE result_models IS 'Stores LLM model names used to generate results';
COMMENT ON COLUMN result_models.name IS 'Unique model name (e.g., gpt-4, claude-sonnet-3.5)';
COMMENT ON COLUMN results.model_id IS 'Foreign key to result_models table, nullable for legacy results';
