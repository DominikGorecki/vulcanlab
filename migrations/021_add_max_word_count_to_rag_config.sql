-- Migration 021: Add max_word_count to RAG config and deprecate old enrichment settings
-- This migration:
-- 1. Adds max_word_count: 750 to retrieval section of all existing RAG config presets
-- 2. Moves deprecated retrieval keys (min_char_count, min_content_length, enrich_lines_above, enrich_lines_below) to _deprecated
-- 3. Moves deprecated consolidation key (enrich_from_md) to _deprecated
-- 4. Is idempotent (safe to run multiple times)

-- Step 1: Add max_word_count to retrieval section if not already present
UPDATE rag_config
SET config = jsonb_set(
    config,
    '{retrieval,max_word_count}',
    '750'::jsonb,
    true
)
WHERE config ? 'retrieval'
  AND NOT (config->'retrieval' ? 'max_word_count');

-- Step 2: Move deprecated retrieval keys to _deprecated nested object
-- We need to handle this carefully to preserve existing _deprecated keys and avoid duplication

-- First, create the _deprecated object with deprecated keys if they exist
UPDATE rag_config
SET config = jsonb_set(
    config,
    '{retrieval,_deprecated}',
    COALESCE(
        config->'retrieval'->'_deprecated',
        '{}'::jsonb
    ) ||
    jsonb_strip_nulls(jsonb_build_object(
        'min_char_count', config->'retrieval'->'min_char_count',
        'min_content_length', config->'retrieval'->'min_content_length',
        'enrich_lines_above', config->'retrieval'->'enrich_lines_above',
        'enrich_lines_below', config->'retrieval'->'enrich_lines_below'
    )),
    true
)
WHERE config ? 'retrieval'
  AND (
    config->'retrieval' ? 'min_char_count' OR
    config->'retrieval' ? 'min_content_length' OR
    config->'retrieval' ? 'enrich_lines_above' OR
    config->'retrieval' ? 'enrich_lines_below'
  );

-- Now remove the deprecated keys from the retrieval section
UPDATE rag_config
SET config = config #- '{retrieval,min_char_count}'
WHERE config->'retrieval' ? 'min_char_count';

UPDATE rag_config
SET config = config #- '{retrieval,min_content_length}'
WHERE config->'retrieval' ? 'min_content_length';

UPDATE rag_config
SET config = config #- '{retrieval,enrich_lines_above}'
WHERE config->'retrieval' ? 'enrich_lines_above';

UPDATE rag_config
SET config = config #- '{retrieval,enrich_lines_below}'
WHERE config->'retrieval' ? 'enrich_lines_below';

-- Step 3: Move deprecated consolidation key (enrich_from_md) to _deprecated nested object

-- Create the _deprecated object with enrich_from_md if it exists
UPDATE rag_config
SET config = jsonb_set(
    config,
    '{consolidation,_deprecated}',
    COALESCE(
        config->'consolidation'->'_deprecated',
        '{}'::jsonb
    ) ||
    jsonb_build_object(
        'enrich_from_md', config->'consolidation'->'enrich_from_md'
    ),
    true
)
WHERE config ? 'consolidation'
  AND config->'consolidation' ? 'enrich_from_md';

-- Remove enrich_from_md from consolidation section
UPDATE rag_config
SET config = config #- '{consolidation,enrich_from_md}'
WHERE config->'consolidation' ? 'enrich_from_md';

-- Validation query to verify migration results
-- Uncomment to run after migration:
/*
SELECT
    preset_name,
    config->'retrieval'->'max_word_count' as max_word_count,
    config->'retrieval'->'_deprecated' as retrieval_deprecated,
    config->'consolidation'->'_deprecated' as consolidation_deprecated,
    -- Verify deprecated keys are gone from main sections
    config->'retrieval' ? 'min_char_count' as has_min_char_count,
    config->'retrieval' ? 'min_content_length' as has_min_content_length,
    config->'retrieval' ? 'enrich_lines_above' as has_enrich_lines_above,
    config->'retrieval' ? 'enrich_lines_below' as has_enrich_lines_below,
    config->'consolidation' ? 'enrich_from_md' as has_enrich_from_md
FROM rag_config
ORDER BY preset_name;
*/

-- Expected results:
-- - All presets should have max_word_count: 750 in retrieval section
-- - Deprecated retrieval keys should be in retrieval._deprecated
-- - Deprecated consolidation key should be in consolidation._deprecated
-- - No deprecated keys should exist in main retrieval or consolidation sections
-- - All other config values should be preserved unchanged
