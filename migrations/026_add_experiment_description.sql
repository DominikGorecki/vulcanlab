-- Migration 026: Add experiment description field
-- This migration adds a general description column to the experiments table
-- to allow users to provide an overall description of the experiment.

-- Add description column to experiments table
ALTER TABLE experiments
ADD COLUMN IF NOT EXISTS description TEXT;

-- Add comment to new column
COMMENT ON COLUMN experiments.description IS 'Overall description of the experiment';
