-- Migration: Add clean_retrieval_context column to queries
-- Run this migration on existing databases

-- Add clean_retrieval_context column to queries table
ALTER TABLE queries ADD COLUMN IF NOT EXISTS clean_retrieval_context JSON;
