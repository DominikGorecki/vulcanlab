-- Migration: Add chunks table with pgvector support
-- Run this script on existing databases to add the chunks table
-- This is non-destructive and will not affect existing tables

-- Enable pgvector extension (if not already enabled)
CREATE EXTENSION IF NOT EXISTS vector;

-- Create chunks table
CREATE TABLE IF NOT EXISTS chunks (
    id SERIAL PRIMARY KEY,
    parent_id INTEGER REFERENCES chunks(id) ON DELETE CASCADE,
    work_id INTEGER NOT NULL REFERENCES works(id) ON DELETE CASCADE,
    level VARCHAR(20) NOT NULL,
    content TEXT NOT NULL,
    embedding vector(768),
    start_line INTEGER NOT NULL,
    end_line INTEGER NOT NULL,
    vector_status VARCHAR(10) NOT NULL DEFAULT 'no_vec'
);

-- Create indexes
CREATE INDEX IF NOT EXISTS ix_chunks_parent_id ON chunks(parent_id);
CREATE INDEX IF NOT EXISTS ix_chunks_work_id ON chunks(work_id);
CREATE INDEX IF NOT EXISTS ix_chunks_level ON chunks(level);
CREATE INDEX IF NOT EXISTS ix_chunks_vector_status ON chunks(vector_status);

-- Create HNSW index for vector similarity search
CREATE INDEX IF NOT EXISTS ix_chunks_embedding_hnsw
ON chunks USING hnsw (embedding vector_cosine_ops);

-- Verify table was created
SELECT 'chunks table created successfully' AS status
WHERE EXISTS (SELECT 1 FROM information_schema.tables WHERE table_name = 'chunks');
