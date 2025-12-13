-- Migration 016: Create tables for simple conversion pipeline
-- Description: Creates parsed_markdown, sanitized_markdown, and heading_modifications tables
--              Adds simple_conversion flag to io_files table
--              Seeds two new prompt templates for simple conversion

BEGIN;

-- Create ENUMs
DO $$ BEGIN
    CREATE TYPE file_type AS ENUM ('pdf', 'epub');
EXCEPTION
    WHEN duplicate_object THEN null;
END $$;

DO $$ BEGIN
    CREATE TYPE document_classification AS ENUM ('small', 'large');
EXCEPTION
    WHEN duplicate_object THEN null;
END $$;

DO $$ BEGIN
    CREATE TYPE modification_action AS ENUM ('remove', 'change', 'keep');
EXCEPTION
    WHEN duplicate_object THEN null;
END $$;

-- Create parsed_markdown table
CREATE TABLE IF NOT EXISTS parsed_markdown (
    id SERIAL PRIMARY KEY,
    work_id INTEGER NOT NULL REFERENCES works(id) ON DELETE CASCADE,
    content BYTEA NOT NULL,  -- Stores compressed markdown
    file_type file_type NOT NULL,
    classification document_classification NOT NULL,
    token_count INTEGER NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP NOT NULL
);

CREATE INDEX IF NOT EXISTS ix_parsed_markdown_work_id ON parsed_markdown(work_id);

-- Create sanitized_markdown table
CREATE TABLE IF NOT EXISTS sanitized_markdown (
    id SERIAL PRIMARY KEY,
    work_id INTEGER NOT NULL REFERENCES works(id) ON DELETE CASCADE,
    content BYTEA NOT NULL,  -- Stores compressed markdown
    token_count INTEGER NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP NOT NULL
);

CREATE INDEX IF NOT EXISTS ix_sanitized_markdown_work_id ON sanitized_markdown(work_id);

-- Create heading_modifications table
CREATE TABLE IF NOT EXISTS heading_modifications (
    id SERIAL PRIMARY KEY,
    work_id INTEGER NOT NULL REFERENCES works(id) ON DELETE CASCADE,
    line_number INTEGER NOT NULL,
    original_heading TEXT NOT NULL,
    modified_heading TEXT,
    action modification_action NOT NULL,
    vectorize_flag BOOLEAN NOT NULL DEFAULT FALSE,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP NOT NULL
);

CREATE INDEX IF NOT EXISTS ix_heading_modifications_work_id ON heading_modifications(work_id);
CREATE INDEX IF NOT EXISTS ix_heading_modifications_work_line ON heading_modifications(work_id, line_number);

-- Add simple_conversion flag to io_files
ALTER TABLE io_files ADD COLUMN IF NOT EXISTS simple_conversion BOOLEAN DEFAULT FALSE;

-- Seed simple conversion prompt templates
-- Note: Only insert if they don't already exist

INSERT INTO prompt_templates (function_tag, version, title, template_content, is_active, created_at, updated_at)
SELECT
    'simple_sanitize_small',
    1,
    'Simple Conversion - Small Document Sanitization',
    'You are an expert document processor preparing academic and research documents for a Retrieval-Augmented Generation (RAG) system.

Your task is to process the provided markdown document to ensure it has:
1. **Proper document hierarchy**: Adjust title heading levels to create appropriate nesting based on context.
2. **Clean, RAG-relevant content**: Remove all non-topical content and fix conversion artifacts.

## Instructions

### Hierarchy Adjustments
- Review all headings (lines starting with #, ##, ###, etc.)
- If a heading is NOT actually a title (e.g., page numbers, "References", "Table of Contents"), REMOVE the heading markers (delete the #''s entirely)
- For actual titles, adjust heading levels (H1-H6) to create proper nesting based on semantic relationships
- Ensure logical hierarchy: child sections should be one level deeper than their parent

### Content Sanitization
- **Fix conversion artifacts**: Replace poorly converted symbols/glyphs with correct text using surrounding context
- **Remove meta-information**: Delete download sources, file metadata, copyright notices
- **Remove non-topical sections**: Delete References, Acknowledgments, Table of Contents, page numbers, headers/footers
- **Remove gibberish**: Delete any garbled text that resulted from poor OCR or conversion
- **Preserve RAG-relevant content**: Keep all substantive text related to the document''s main topics

### Output Format
- Return ONLY the sanitized markdown
- Do NOT add explanations, comments, or metadata
- Do NOT wrap output in code blocks or additional formatting
- Maintain markdown syntax (headings with #, lists, emphasis, etc.)

---

## Document to Process

{markdown}

---

## Sanitized Output',
    TRUE,
    NOW(),
    NOW()
WHERE NOT EXISTS (
    SELECT 1 FROM prompt_templates WHERE function_tag = 'simple_sanitize_small'
);

INSERT INTO prompt_templates (function_tag, version, title, template_content, is_active, created_at, updated_at)
SELECT
    'simple_sanitize_large',
    1,
    'Simple Conversion - Large Document Analysis',
    'You are an expert document processor analyzing a large document''s structure for a RAG system.

You will receive a CONDENSED representation showing each heading with contextual sentences. Your task is to provide heading-level modifications.

## Instructions

For each heading, determine:

1. **Action**: Choose one:
   - `KEEP`: Heading is valid, keep as-is
   - `CHANGE`: Heading should be modified (level change, text cleanup)
   - `REMOVE`: Not a real heading (e.g., page numbers, "References")

2. **Modified Heading**: If action=CHANGE, provide the corrected heading with proper markdown level markers (#, ##, ###)
   - Adjust heading level for proper hierarchy
   - Clean up formatting issues (extra spaces, weird characters)
   - If action=REMOVE or action=KEEP, leave this blank

3. **Vectorize**: Choose one:
   - `VECTORIZE`: This section contains RAG-relevant content and should be indexed
   - `SKIP`: This section is not relevant (meta-information, acknowledgments, etc.)

## Output Format

Provide your modifications as a structured list, one per heading:

```
LINE: {line_number}
ACTION: {KEEP|CHANGE|REMOVE}
MODIFIED: {new heading if ACTION=CHANGE, otherwise blank}
VECTORIZE: {VECTORIZE|SKIP}
---
```

## Example

Input:
```
5: ## Introduction
  This paper presents a novel approach to machine learning. We focus on neural networks.
  ...
  The rest of the paper is organized as follows.

12: ### Page 3
  Lorem ipsum dolor sit amet.
```

Output:
```
LINE: 5
ACTION: KEEP
MODIFIED:
VECTORIZE: VECTORIZE
---
LINE: 12
ACTION: REMOVE
MODIFIED:
VECTORIZE: SKIP
---
```

---

## Condensed Document

{condensed_document}

---

## Your Modifications',
    TRUE,
    NOW(),
    NOW()
WHERE NOT EXISTS (
    SELECT 1 FROM prompt_templates WHERE function_tag = 'simple_sanitize_large'
);

COMMIT;
