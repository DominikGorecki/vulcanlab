-- Migration 024: Add automatic evaluation mode support
-- This migration adds columns to support automatic evaluation mode where
-- answer generation and judging use different LLM providers.

-- Add automatic mode configuration columns to experiments table
ALTER TABLE experiments
ADD COLUMN IF NOT EXISTS auto_mode_enabled BOOLEAN NOT NULL DEFAULT FALSE,
ADD COLUMN IF NOT EXISTS auto_answer_provider VARCHAR(50),
ADD COLUMN IF NOT EXISTS auto_judge_provider VARCHAR(50);

-- Add CHECK constraint: if auto_mode_enabled is true, both provider fields must be non-null
ALTER TABLE experiments
ADD CONSTRAINT chk_auto_mode_providers
CHECK (
    (auto_mode_enabled = FALSE) OR
    (auto_mode_enabled = TRUE AND auto_answer_provider IS NOT NULL AND auto_judge_provider IS NOT NULL)
);

-- Add prompt_group_id to experiment_prompts for grouping related prompts
-- (main, answer_x, answer_y prompts in automatic mode)
ALTER TABLE experiment_prompts
ADD COLUMN IF NOT EXISTS prompt_group_id INTEGER;

-- Create index on (experiment_id, prompt_group_id) for efficient grouped prompt queries
CREATE INDEX IF NOT EXISTS idx_experiment_prompts_group
ON experiment_prompts(experiment_id, prompt_group_id)
WHERE prompt_group_id IS NOT NULL;

-- Add comments to new columns
COMMENT ON COLUMN experiments.auto_mode_enabled IS 'Whether automatic evaluation mode is enabled';
COMMENT ON COLUMN experiments.auto_answer_provider IS 'Provider for answer generation (openai or gemini)';
COMMENT ON COLUMN experiments.auto_judge_provider IS 'Provider for judge evaluation (opposite of answer provider)';
COMMENT ON COLUMN experiment_prompts.prompt_group_id IS 'Groups related prompts (main, answer_x, answer_y) in automatic mode';
