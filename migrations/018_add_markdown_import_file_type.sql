-- Migration 018: Add markdown_import to file_type enum
-- Description: Adds 'markdown_import' value to the file_type enum for markdown import functionality

BEGIN;

-- Add markdown_import to file_type enum
ALTER TYPE file_type ADD VALUE IF NOT EXISTS 'markdown_import';

COMMIT;
