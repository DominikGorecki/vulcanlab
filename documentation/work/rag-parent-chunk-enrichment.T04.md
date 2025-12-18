# Ticket: rag-parent-chunk-enrichment.T04 - Migration Script for Existing RAG Configs

## Source
- Spec: documentation/work/rag-parent-chunk-enrichment.spec.md
- Patterns: documentation/patterns.md

## Goal
- Create SQL migration to add `max_word_count` to all existing RAG config presets
- Move deprecated settings to `_deprecated` nested object for backwards compatibility
- Ensure migration is idempotent and safe for production use

## Scope
### In scope
- Create migration file `migrations/021_add_max_word_count_to_rag_config.sql`
- Add `max_word_count: 750` to retrieval section of all existing presets
- Move deprecated keys (`min_char_count`, `min_content_length`, `enrich_lines_above`, `enrich_lines_below`) to `_deprecated` in retrieval section
- Move deprecated key (`enrich_from_md`) to `_deprecated` in consolidation section
- Ensure idempotency (can run multiple times without errors)
- Unit tests for migration logic

### Out of scope
- Schema changes to rag_config table structure
- Changes to init_db.py (T05)
- UI changes (T06)
- Application code changes (handled in T02, T03)

## Dependencies
- Depends on: none (database-only)
- Unblocks: T05 (Update init_db.py)

## Implementation plan
1. Create migration file `migrations/021_add_max_word_count_to_rag_config.sql`
2. Write SQL to update all rows in `rag_config` table:
   - Use JSONB operators to add `max_word_count: 750` to `config->'retrieval'`
   - Check if key already exists (idempotency)
   - Move deprecated keys to `config->'retrieval'->'_deprecated'`
   - Move `enrich_from_md` to `config->'consolidation'->'_deprecated'`
3. Add safeguards:
   - WHERE clause to only update rows that need changes
   - Use `jsonb_set()` and `jsonb_build_object()` for safe updates
   - Preserve all other config values
4. Write migration validation query to verify changes
5. Create unit test to verify migration logic:
   - Use in-memory SQLite or pytest fixtures
   - Test idempotency (run twice, verify no errors or duplicate updates)
   - Test preservation of other config values
   - Test handling of missing sections

Patterns to apply:
- SQL Migrations - Follow pattern from `migrations/013_create_rag_config.sql`
- Database - Use PostgreSQL JSONB operators

Deviations (if any):
- None

## Unit tests (required)
- Add tests for:
  - Migration adds `max_word_count: 750` to all presets' retrieval section
  - Migration is idempotent (can run twice without errors)
  - Migration preserves other retrieval config values
  - Migration preserves other consolidation config values
  - Migration handles presets with missing retrieval section gracefully
  - Migration handles presets with missing consolidation section gracefully
  - Deprecated keys moved to `_deprecated` object correctly
  - Deprecated keys not duplicated if already in `_deprecated`

- Suggested locations:
  - `tests/unit/test_migration_021.py`

- Mocking/fakes needed:
  - Use in-memory SQLite database with rag_config table
  - Or use pytest fixtures with PostgreSQL test database
  - Mock config table with sample presets

## Acceptance criteria (checklist)
- [ ] Migration file `migrations/021_add_max_word_count_to_rag_config.sql` created
- [ ] SQL adds `max_word_count: 750` to all presets' `config->'retrieval'`
- [ ] Deprecated retrieval keys moved to `config->'retrieval'->'_deprecated'`
- [ ] Deprecated consolidation key moved to `config->'consolidation'->'_deprecated'`
- [ ] Migration is idempotent (safe to run multiple times)
- [ ] Migration preserves all other config values
- [ ] Migration handles missing sections gracefully
- [ ] Validation query included in migration file
- [ ] All unit tests pass
- [ ] Migration tested on copy of production data (manual verification step)

## Manual verification
- Steps:
  1. Create test database with sample rag_config rows
  2. Insert presets with various config structures (some missing sections)
  3. Run migration: `psql -f migrations/021_add_max_word_count_to_rag_config.sql`
  4. Query rag_config table to verify updates
  5. Run migration again to verify idempotency
  6. Check that deprecated keys are in `_deprecated` nested objects

- Expected results:
  - All presets have `max_word_count: 750` in retrieval section
  - Deprecated keys moved to `_deprecated` objects
  - Other config values unchanged
  - No errors on second run (idempotent)

## Notes
- PostgreSQL JSONB update syntax example:
  ```sql
  UPDATE rag_config
  SET config = jsonb_set(
    config,
    '{retrieval,max_word_count}',
    '750',
    true
  )
  WHERE config->'retrieval' IS NOT NULL
    AND config->'retrieval'->'max_word_count' IS NULL;
  ```
- Deprecated keys to move in retrieval: `min_char_count`, `min_content_length`, `enrich_lines_above`, `enrich_lines_below`
- Deprecated key to move in consolidation: `enrich_from_md`
- Use `jsonb_build_object()` to create `_deprecated` nested object
- Check if `_deprecated` already exists before creating
- Include helpful comments in SQL file explaining each step
- Migration should run as app user (not admin) per spec requirements
- Reference existing migrations like `013_create_rag_config.sql` for structure and style
