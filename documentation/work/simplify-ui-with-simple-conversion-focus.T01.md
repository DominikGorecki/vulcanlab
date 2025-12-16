# Ticket: simplify-ui-with-simple-conversion-focus.T01 - Database Migration for History Query Indexes

## Source
- Spec: documentation/work/simplify-ui-with-simple-conversion-focus.spec.md
- Patterns: documentation/patterns.md

## Goal
- Create database migration 017 with indexes to support efficient simple conversion history queries
- Add general timestamp sorting index and partial index for filtered simple conversion queries
- Update init_db.py to include new indexes for fresh database installations

## Scope
### In scope
- SQL migration file creating ix_works_created_at index on works.created_at DESC
- SQL migration file creating ix_works_simple_conversion_created_at partial index for simple conversion filtering
- Update to init_db.py to include both new indexes in schema initialization
- Migration script that checks if indexes already exist before creating

### Out of scope
- Changing existing migration files
- Modifying any table schemas or columns
- Adding data migrations or backfill operations
- Performance testing (will be validated in later tickets)

## Dependencies
- Depends on: none (foundational infrastructure)
- Unblocks: T02, T03 (backend endpoints need indexes for performance)

## Implementation plan
1. Create migration file migrations/017_add_history_indexes.sql with two index definitions
2. Add ix_works_created_at general index for timestamp sorting (CREATE INDEX IF NOT EXISTS)
3. Add ix_works_simple_conversion_created_at partial index with WHERE clause filtering on processing_status ? 'simple_conversion_mode'
4. Include DROP INDEX IF EXISTS statements for rollback capability
5. Locate init_db.py file (likely in src/vulcanlab/data/ or scripts/)
6. Add both index creation statements to the schema initialization section
7. Ensure indexes use IF NOT EXISTS to be idempotent
8. Add comments explaining the purpose of each index

- Patterns to apply:
  - **Database Migrations** - SQL-based migrations for schema changes, numbered sequentially
  - **Idempotent Operations** - Use IF NOT EXISTS/IF EXISTS for safe reruns
  - **Partial Indexes** - Optimize specific query patterns with WHERE clause constraints

- Deviations (if any):
  - None - follows established migration pattern

## Unit tests (required)
- Add tests for:
  - Migration 017 can be applied to a fresh database without errors
  - Migration 017 can be applied idempotently (running twice does not fail)
  - Indexes exist after migration (query pg_indexes table)
  - Partial index WHERE clause is correctly applied (verify in pg_indexes)
  - init_db.py creates both indexes when initializing fresh database
- Suggested locations:
  - tests/unit/test_migration_017.py (new file)
  - tests/unit/test_init_db.py (extend existing or create if needed)
- Mocking/fakes needed:
  - Mock database connection for migration script testing
  - In-memory SQLite or test PostgreSQL instance for actual index creation verification

## Acceptance criteria (checklist)
- [ ] Migration file migrations/017_add_history_indexes.sql exists
- [ ] Migration creates ix_works_created_at index on works(created_at DESC)
- [ ] Migration creates ix_works_simple_conversion_created_at partial index with JSON filter
- [ ] Both indexes use IF NOT EXISTS for idempotency
- [ ] Migration includes DROP INDEX statements for rollback
- [ ] init_db.py updated to create both indexes during fresh install
- [ ] Unit tests verify migration can be applied successfully
- [ ] Unit tests verify indexes exist after migration
- [ ] Unit tests verify init_db.py creates indexes

## Manual verification
- Steps:
  1. Run migration script against test database
  2. Query pg_indexes to verify both indexes exist
  3. Check that ix_works_simple_conversion_created_at has correct WHERE clause
  4. Drop database and run init_db.py to create fresh schema
  5. Verify both indexes exist in fresh database
  6. Run migration again to verify idempotency (no errors)
- Expected results:
  - Both indexes appear in pg_indexes with correct definitions
  - Partial index shows WHERE clause: (processing_status ? 'simple_conversion_mode'::text)
  - No errors on repeated migration runs
  - Fresh database from init_db.py includes both indexes

## Notes
- The partial index is more efficient than a composite index for this specific query pattern because it limits index size to only simple conversion works
- The general ix_works_created_at index supports other timestamp-based queries across all works
- PostgreSQL GIN index on processing_status already exists from migration 008 and works in combination with these new indexes
- Migration numbering: Verify current highest migration number before finalizing file name
- init_db.py location may vary - check src/vulcanlab/data/, scripts/, or root directory
