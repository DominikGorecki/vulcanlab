-- Migration 023: Add template_type column to prompt_templates
-- This migration adds template categorization for eval vs rag templates

-- Add template_type column (nullable for backwards compatibility)
ALTER TABLE prompt_templates
ADD COLUMN IF NOT EXISTS template_type VARCHAR(50);

-- Create index for filtering by type
CREATE INDEX IF NOT EXISTS idx_prompt_templates_type
ON prompt_templates(template_type);

-- Add comment
COMMENT ON COLUMN prompt_templates.template_type
IS 'Template category: rag, eval, or NULL for legacy templates';
