# Ticket: sentence-based-chunk-search-filter.T03 - Add Sentence Filter Settings to RAG Config Schema

## Source
- Spec: documentation/work/sentence-based-chunk-search-filter.spec.md
- Patterns: documentation/patterns.md

## Goal
- Add min_sentence_filter_enabled and min_sentence_count to RAG config JSONB schema
- Update default RAG config seed data to include new fields
- Ensure API validation accepts and validates the new fields

## Scope
### In scope
- Update migrations/013_create_rag_config.sql to include new fields in default preset INSERT
- Add validation in src/vulcanlab_api/schemas/rag_config.py for new fields
- Document the new fields in RagConfig model docstring
- Set defaults: min_sentence_filter_enabled=false, min_sentence_count=5

### Out of scope
- UI components (separate ticket)
- Retrieval logic changes (separate ticket)
- Migration to update existing rag_config rows (if needed, handle manually or in separate script)

## Dependencies
- Depends on: none (independent schema change)
- Unblocks: T04 (retrieval logic needs config fields), T06 (UI needs schema)

## Implementation plan
- Read migrations/013_create_rag_config.sql to understand current default config structure
- Update the INSERT statement for default preset to include in retrieval section:
  ```json
  "retrieval": {
    "min_sentence_filter_enabled": false,
    "min_sentence_count": 5,
    ... existing fields
  }
  ```
- Update src/vulcanlab_api/schemas/rag_config.py:
  - Locate the Pydantic schema for RAG config retrieval section
  - Add min_sentence_filter_enabled: bool field
  - Add min_sentence_count: int field with validation (>= 1)
  - Add Field descriptions for documentation
- Update RagConfig model docstring in src/vulcanlab/data/models/rag_config.py to document new fields
- Patterns to apply:
  - Configuration Dual System: New fields in vulcanlab.config (RagConfig JSONB), not API config
  - API Layer validation: Use Pydantic schemas for request validation
- Deviations (if any):
  - None

## Unit tests (required)
- Add tests for:
  - RagConfig schema validates min_sentence_filter_enabled as boolean
  - RagConfig schema validates min_sentence_count >= 1 (reject 0, -1)
  - RagConfig schema accepts valid config with new fields
  - Default config includes min_sentence_filter_enabled=false
  - Default config includes min_sentence_count=5
  - API endpoint returns config with new fields (integration-style test with mocked DB)
  - API endpoint rejects invalid min_sentence_count (< 1)
- Suggested locations:
  - tests/unit/test_rag_config_schema.py (create if doesn't exist)
  - tests/unit/test_rag_config_api.py (for API validation)
- Mocking/fakes needed:
  - Mock database session for API tests
  - No real database connection

## Acceptance criteria (checklist)
- [ ] migrations/013_create_rag_config.sql updated with new fields in default preset
- [ ] Pydantic schema in schemas/rag_config.py includes new fields
- [ ] Validation enforces min_sentence_count >= 1
- [ ] RagConfig model docstring documents new fields
- [ ] Default values: min_sentence_filter_enabled=false, min_sentence_count=5
- [ ] Unit tests pass for schema validation
- [ ] API accepts valid updates to new fields
- [ ] API rejects invalid values (min_sentence_count < 1)

## Manual verification
- Steps:
  1. Run migration 013 on fresh test database to create rag_config table
  2. Query: SELECT config FROM rag_config WHERE is_default=true;
  3. Verify JSON includes retrieval.min_sentence_filter_enabled and min_sentence_count
  4. Use API to GET /api/v1/rag-config (or equivalent endpoint)
  5. Verify response includes new fields
  6. Use API to PUT update with min_sentence_count=10
  7. Verify update succeeds
  8. Use API to PUT update with min_sentence_count=0
  9. Verify validation error returned
- Expected results:
  - Default config includes new fields with correct defaults
  - API returns new fields in GET responses
  - API validates and accepts valid updates
  - API rejects invalid values with clear error message

## Notes
- The RagConfig table stores config as JSONB, so schema is flexible
- For existing databases, the default config row may need manual update or a small migration script
- The spec answers: default is min_sentence_filter_enabled=false (backward compatible)
- No maximum validation needed per user answer (allow any positive integer)
