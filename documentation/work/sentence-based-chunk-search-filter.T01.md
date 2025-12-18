# Ticket: sentence-based-chunk-search-filter.T01 - Add sentence_count Column to Chunk Model and Database Schema

## Source
- Spec: documentation/work/sentence-based-chunk-search-filter.spec.md
- Patterns: documentation/patterns.md

## Goal
- Add sentence_count column to chunks table via migration SQL
- Update Chunk SQLAlchemy model to include the new field
- Ensure fresh installs include the column without needing migrations

## Scope
### In scope
- Create migration SQL file (019_add_sentence_count.sql) with DDL changes
- Add sentence_count field to Chunk model in src/vulcanlab/data/models/chunk.py
- Add index creation SQL for sentence_count column
- Include rollback SQL in migration comments
- Verify model and database schema are aligned

### Out of scope
- Populating sentence_count values (handled in separate backfill ticket)
- Modifying chunking logic to set sentence_count
- UI or API changes

## Dependencies
- Depends on: none
- Unblocks: T02, T03, T04

## Implementation plan
- Review existing migration files (013_create_rag_config.sql, 001_add_chunks_table.sql) for pattern consistency
- Create migrations/019_add_sentence_count.sql with:
  - ALTER TABLE chunks ADD COLUMN sentence_count INTEGER NULL;
  - CREATE INDEX idx_chunks_sentence_count ON chunks(sentence_count);
  - Comment block documenting rollback: DROP INDEX and DROP COLUMN
- Update src/vulcanlab/data/models/chunk.py:
  - Add sentence_count: Mapped[Optional[int]] = mapped_column(Integer, nullable=True, index=True)
  - Update docstring to document the new field
- Verify the migration can be run idempotently (use IF NOT EXISTS where applicable)
- Patterns to apply:
  - Database Patterns: Use SQLAlchemy declarative models in src/vulcanlab/data/models
  - SQL migrations: DDL changes in .sql file as per existing migration pattern
- Deviations (if any):
  - None

## Unit tests (required)
- Add tests for:
  - Chunk model has sentence_count attribute (type check)
  - sentence_count is nullable (accepts None)
  - sentence_count accepts integer values
  - Model instantiation with sentence_count=None works
  - Model instantiation with sentence_count=5 works
- Suggested locations:
  - tests/unit/test_chunk_model.py (create if doesn't exist)
- Mocking/fakes needed:
  - Mock database session for model tests
  - No actual database connection needed (unit test)

## Acceptance criteria (checklist)
- [ ] Migration file migrations/019_add_sentence_count.sql created
- [ ] Migration includes ALTER TABLE to add sentence_count column (INTEGER, NULL)
- [ ] Migration includes CREATE INDEX for sentence_count
- [ ] Migration includes rollback instructions in comments
- [ ] Chunk model updated with sentence_count field (Optional[int])
- [ ] Chunk model docstring updated to document sentence_count
- [ ] Unit tests pass for Chunk model with new field
- [ ] Migration SQL is idempotent (safe to re-run)

## Manual verification
- Steps:
  1. Run the migration SQL against test database: psql -U user -d dbname -f migrations/019_add_sentence_count.sql
  2. Verify column exists: \d chunks (should show sentence_count column)
  3. Verify index exists: \di (should show idx_chunks_sentence_count)
  4. Insert a test chunk with sentence_count=5
  5. Query the chunk and verify sentence_count is stored correctly
- Expected results:
  - Column sentence_count appears in chunks table schema
  - Index idx_chunks_sentence_count exists
  - Can insert and query chunks with sentence_count values
  - Can insert chunks with sentence_count=NULL

## Notes
- Follow the pattern from migration 010 which also added a column to chunks table
- The column must be nullable to support legacy chunks and error cases
- Index is B-tree by default in PostgreSQL, no need to specify type
- This is a pure schema change ticket - no application logic changes
