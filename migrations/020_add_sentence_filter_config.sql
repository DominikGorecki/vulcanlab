-- Migration 020: Add sentence filter fields to RAG config
-- Adds min_sentence_filter_enabled and min_sentence_count to retrieval section of default RAG config

-- Update the default RAG config preset to include sentence filter fields
UPDATE rag_config
SET config = jsonb_set(
    jsonb_set(
        config,
        '{retrieval,min_sentence_filter_enabled}',
        'false'::jsonb
    ),
    '{retrieval,min_sentence_count}',
    '5'::jsonb
)
WHERE config ? 'retrieval';