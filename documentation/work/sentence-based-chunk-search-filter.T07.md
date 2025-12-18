# Ticket: sentence-based-chunk-search-filter.T07 - Update db_init.py for Fresh Installs

## Source
- Spec: documentation/work/sentence-based-chunk-search-filter.spec.md
- Patterns: documentation/patterns.md

## Goal
- Ensure fresh database installations include sentence_count column and index without needing migrations
- Update db_init.py (or equivalent initialization script) to match migration 019 schema

## Scope
### In scope
- Locate and update database initialization script that creates chunks table
- Add sentence_count column definition (INTEGER NULL)
- Add index creation for idx_chunks_sentence_count
- Ensure default RAG config seed data includes new fields

### Out of scope
- Modifying migration files (already complete in T01)
- Changing existing database upgrade paths

## Dependencies
- Depends on: T01 (migration defines schema), T03 (RAG config schema)
- Unblocks: Fresh installs without migration requirement

## Implementation plan
- Search codebase for database initialization script (likely in src/vulcanlab/data/ or migrations/)
- Common patterns: db_init.py, init_db.py, or SQL file like 000_initial_schema.sql
- Locate chunks table creation statement
- Add sentence_count column:
  ```sql
  sentence_count INTEGER NULL,
  ```
- Add index creation (either in same statement or separate):
  ```sql
  CREATE INDEX idx_chunks_sentence_count ON chunks(sentence_count);
  ```
- Locate RAG config default seed data insertion
- Ensure default config includes min_sentence_filter_enabled=false, min_sentence_count=5 in retrieval section
- Verify initialization script creates table with all columns matching current schema after migration 019
- Patterns to apply:
  - Infrastructure: Fresh install scripts should match migrated schema
  - Database Patterns: SQL-based or SQLAlchemy create_all() patterns
- Deviations (if any):
  - None

## Unit tests (required)
- Add tests for:
  - Fresh database initialization creates chunks table with sentence_count column
  - Fresh database initialization creates idx_chunks_sentence_count index
  - Fresh database initialization seeds RAG config with new fields
  - Chunk table schema matches migration 019 schema exactly
- Suggested locations:
  - tests/unit/test_db_init.py (create if doesn't exist)
  - Or tests/docker/test_db_init.py if initialization testing is integration-style
- Mocking/fakes needed:
  - Test database or in-memory SQLite for unit tests
  - For integration tests: Docker PostgreSQL container (but spec says no integration tests in tickets)
  - Stick to unit tests with mocked database

## Acceptance criteria (checklist)
- [ ] Database initialization script updated with sentence_count column
- [ ] Database initialization script creates idx_chunks_sentence_count index
- [ ] Default RAG config seed data includes new retrieval fields
- [ ] Fresh database schema matches migration 019 result
- [ ] Unit tests verify column and index creation
- [ ] Documentation or comments note the schema version

## Manual verification
- Steps:
  1. Drop test database: dropdb test_vulcanlab
  2. Create fresh database: createdb test_vulcanlab
  3. Run database initialization script (e.g., python -m vulcanlab.data.db_init)
  4. Connect to database: psql test_vulcanlab
  5. Verify chunks table: \d chunks (should show sentence_count column)
  6. Verify index: \di (should show idx_chunks_sentence_count)
  7. Query RAG config: SELECT config FROM rag_config WHERE is_default=true;
  8. Verify config includes min_sentence_filter_enabled and min_sentence_count
- Expected results:
  - Fresh database has sentence_count column in chunks table
  - Index idx_chunks_sentence_count exists
  - Default RAG config includes new fields with correct defaults
  - Schema matches post-migration-019 state exactly

## Notes
- This ensures new users don't need to run migrations 001-019 on fresh install
- The initialization script should create the final schema state, not replay all migrations
- If db_init doesn't exist, this ticket may need to create it or update Docker initialization SQL
- Check docker/init_db.sql or similar if using Docker-based initialization
