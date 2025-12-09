-- Migration 009: Create results table for storing LLM responses
--
-- This table stores LLM-generated responses linked to queries.
-- One query can have many results (one-to-many relationship).

-- Create results table
CREATE TABLE IF NOT EXISTS results (
    id SERIAL PRIMARY KEY,
    query_id INTEGER NOT NULL REFERENCES queries(id) ON DELETE CASCADE,
    response_text TEXT NOT NULL,
    created_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT NOW()
);

-- Create index on query_id for efficient lookups
CREATE INDEX IF NOT EXISTS ix_results_query_id ON results(query_id);

-- Create index on created_at for ordering
CREATE INDEX IF NOT EXISTS ix_results_created_at ON results(created_at);

-- Grant permissions to app user
-- (Assuming psych_rag_app_user_test is the app user, adjust if needed)
GRANT SELECT, INSERT, UPDATE, DELETE ON results TO psych_rag_app_user_test;
GRANT USAGE, SELECT ON SEQUENCE results_id_seq TO psych_rag_app_user_test;

