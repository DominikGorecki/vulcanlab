# Ticket: rag-parent-chunk-enrichment.T05 - Update init_db.py for Fresh Installs

## Source
- Spec: documentation/work/rag-parent-chunk-enrichment.spec.md
- Patterns: documentation/patterns.md

## Goal
- Update `src/vulcanlab/data/init_db.py` to create clean RAG config schema without deprecated keys
- Ensure fresh installs use the new configuration structure
- Add `max_word_count` to default preset retrieval settings

## Scope
### In scope
- Update `create_default_rag_config()` function in `src/vulcanlab/data/init_db.py`
- Add `max_word_count: 750` to retrieval section
- Remove deprecated keys from default config template
- Ensure coverage_threshold is present in consolidation section
- Unit tests for default config structure

### Out of scope
- Migration of existing configs (T04)
- UI changes (T06)
- Database schema changes
- Changes to retrieval or consolidation logic

## Dependencies
- Depends on: T04 (Migration Script)
- Unblocks: T07 (End-to-end Integration)

## Implementation plan
1. Read existing `src/vulcanlab/data/init_db.py` to understand current config creation
2. Locate `create_default_rag_config()` function (or equivalent)
3. Update default config dictionary/object:
   - Add `"max_word_count": 750` to retrieval section
   - Remove `min_char_count` from retrieval (deprecated)
   - Remove `min_content_length` from retrieval (deprecated)
   - Remove `enrich_lines_above` from retrieval (deprecated)
   - Remove `enrich_lines_below` from retrieval (deprecated)
   - Remove `enrich_from_md` from consolidation (deprecated)
   - Ensure `coverage_threshold: 0.5` present in consolidation
4. Verify default config matches spec schema (section "RAG Config Schema (Updated)")
5. Write unit test to validate default config structure
6. Test fresh database initialization

Patterns to apply:
- Core Module Independence - init_db.py operates on database models directly
- Session Management - Uses database session for config insertion

Deviations (if any):
- None

## Unit tests (required)
- Add tests for:
  - Default config includes `max_word_count: 750` in retrieval section
  - Default config does not include deprecated retrieval keys
  - Default config does not include deprecated consolidation keys
  - Default config includes `coverage_threshold` in consolidation section
  - Default config includes all required non-deprecated keys
  - Default config structure matches spec schema
  - `create_default_rag_config()` successfully inserts config into database

- Suggested locations:
  - `tests/unit/test_init_db_default_config.py`

- Mocking/fakes needed:
  - Mock SQLAlchemy Session
  - Mock RagConfig model
  - In-memory database for integration-style unit test (optional)

## Acceptance criteria (checklist)
- [ ] `create_default_rag_config()` updated in `src/vulcanlab/data/init_db.py`
- [ ] `max_word_count: 750` added to retrieval section
- [ ] Deprecated keys removed from default config
- [ ] `coverage_threshold: 0.5` present in consolidation section
- [ ] Default config matches spec schema structure
- [ ] Fresh database initialization creates clean config
- [ ] All unit tests pass
- [ ] Code follows snake_case naming convention

## Manual verification
- Steps:
  1. Drop and recreate test database
  2. Run `init_db.py` (or equivalent initialization script)
  3. Query `rag_config` table for default preset
  4. Verify config structure matches spec
  5. Verify no deprecated keys present
  6. Verify `max_word_count` and `coverage_threshold` present

- Expected results:
  - Default preset created successfully
  - Config has clean structure (no `_deprecated` object)
  - All new required keys present
  - No deprecated keys present

## Notes
- Default config should match the "clean" version in spec section "RAG Config Schema (Updated)"
- Clean config example from spec:
  ```json
  {
    "retrieval": {
      "dense_limit": 19,
      "lexical_limit": 5,
      "rrf_k": 50,
      "top_k_rrf": 75,
      "top_n_final": 17,
      "entity_boost": 0.05,
      "min_word_count": 150,
      "max_word_count": 750,
      "mmr_lambda": 0.7,
      "reranker_batch_size": 8,
      "reranker_max_length": 512,
      "min_sentence_filter_enabled": false,
      "min_sentence_count": 5
    },
    "consolidation": {
      "coverage_threshold": 0.5,
      "line_gap": 7,
      "min_content_length": 350
    },
    "augmentation": {
      "top_n_contexts": 5
    }
  }
  ```
- Note: The spec example shows `min_content_length` in consolidation (not deprecated there)
- Only deprecated in retrieval section
- Ensure init_db.py uses appropriate defaults for all sections
- If config uses Python dict, ensure proper formatting and no typos
- Test with fresh PostgreSQL database to verify full initialization flow
