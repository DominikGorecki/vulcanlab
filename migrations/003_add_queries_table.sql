-- Migration: Add queries table for query expansion results
-- Run this migration on existing databases to add the queries table

-- Create queries table
CREATE TABLE IF NOT EXISTS queries (
    id SERIAL PRIMARY KEY,
    original_query TEXT NOT NULL,
    expanded_queries JSON,
    hyde_answer TEXT,
    intent VARCHAR(50),
    entities JSON,
    embedding_original vector(768),
    embeddings_mqe JSON,
    embedding_hyde vector(768),
    vector_status VARCHAR(10) NOT NULL DEFAULT 'no_vec',
    created_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT NOW()
);

-- Create indexes
CREATE INDEX IF NOT EXISTS ix_queries_intent ON queries (intent);
CREATE INDEX IF NOT EXISTS ix_queries_vector_status ON queries (vector_status);

-- Create HNSW indexes for vector columns
CREATE INDEX IF NOT EXISTS ix_queries_embedding_original_hnsw
    ON queries USING hnsw (embedding_original vector_cosine_ops);
CREATE INDEX IF NOT EXISTS ix_queries_embedding_hyde_hnsw
    ON queries USING hnsw (embedding_hyde vector_cosine_ops);
