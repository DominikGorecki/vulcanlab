-- Migration 007: Create io_files table for tracking input and output files
--
-- This table tracks all files in the input and output directories to avoid
-- repeated hash computations and enable efficient file management.

-- Create enum type for file_type
CREATE TYPE filetype AS ENUM ('input', 'to_convert');

-- Create io_files table
CREATE TABLE IF NOT EXISTS io_files (
    id SERIAL PRIMARY KEY,
    filename VARCHAR NOT NULL,
    file_type filetype NOT NULL,
    file_path VARCHAR NOT NULL UNIQUE,
    created_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT NOW(),
    last_seen_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT NOW()
);

-- Create indexes for efficient querying
CREATE INDEX IF NOT EXISTS ix_io_files_filename ON io_files(filename);
CREATE INDEX IF NOT EXISTS ix_io_files_file_type ON io_files(file_type);
CREATE INDEX IF NOT EXISTS ix_io_files_last_seen_at ON io_files(last_seen_at);

-- Create function to automatically update updated_at timestamp
CREATE OR REPLACE FUNCTION update_io_files_updated_at()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = NOW();
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

-- Create trigger to call the update function
DROP TRIGGER IF EXISTS trigger_update_io_files_updated_at ON io_files;
CREATE TRIGGER trigger_update_io_files_updated_at
    BEFORE UPDATE ON io_files
    FOR EACH ROW
    EXECUTE FUNCTION update_io_files_updated_at();

-- Grant permissions to app user
GRANT SELECT, INSERT, UPDATE, DELETE ON io_files TO psych_rag_app_user_test;
GRANT USAGE, SELECT ON SEQUENCE io_files_id_seq TO psych_rag_app_user_test;
