# Ticket: work-summarization.T02 - Create Summary Tables Migration

## Source

* Spec: documentation/work/work-summarization.spec.md
* Patterns: documentation/patterns.md

## Goal

* Create database migration for summary_nodes table with all required columns and indexes
* Create database migration for work_summaries polymorphic table
* Create database migration for summarize_settings table with default configuration

## Phase

* Migrations

## Scope

### In scope

* Migration file: migrations/029_add_summary_tables.sql
* summary_nodes table with: id, chunk_id, work_id, gist, key_points, definitions, key_terms, examples, start_line, end_line, salience_score, created_at
* work_summaries table with: id, work_id, type, content, line_references, created_at, unique constraint
* summarize_settings table with all salience weight/threshold columns
* Foreign key constraints to chunks and works tables
* Indexes on work_id columns for query performance
* CHECK constraint on work_summaries.type

### Out of scope

* SQLAlchemy ORM models (T03)
* init_db.py updates (T03)
* Seeding default settings (T03)

## Dependencies

* Depends on: none
* Unblocks: T03

## Implementation plan

1. Create migrations/029_add_summary_tables.sql
2. Add summary_nodes table creation with:
   - SERIAL PRIMARY KEY for id
   - INTEGER NOT NULL FK to chunks(id) ON DELETE CASCADE for chunk_id
   - INTEGER NOT NULL FK to works(id) ON DELETE CASCADE for work_id with INDEX
   - TEXT NOT NULL for gist
   - JSONB NOT NULL DEFAULT '[]' for key_points, definitions, key_terms, examples
   - INTEGER NOT NULL for start_line and end_line
   - FLOAT NOT NULL for salience_score
   - TIMESTAMP NOT NULL DEFAULT NOW() for created_at
3. Add work_summaries table creation with:
   - SERIAL PRIMARY KEY for id
   - INTEGER NOT NULL FK to works(id) ON DELETE CASCADE for work_id with INDEX
   - VARCHAR(30) NOT NULL with CHECK constraint for type
   - JSONB NOT NULL for content and line_references
   - TIMESTAMP NOT NULL DEFAULT NOW() for created_at
   - UNIQUE constraint on (work_id, type)
4. Add summarize_settings table creation with:
   - SERIAL PRIMARY KEY for id
   - BOOLEAN DEFAULT true for h1_always_summarize
   - INTEGER DEFAULT 100 for h2_top_percent
   - FLOAT DEFAULT 0.5 for h3_salience_threshold
   - FLOAT DEFAULT 0.7 for h4_salience_threshold
   - FLOAT DEFAULT 0.3/0.2/0.2/0.15/0.15 for weight columns
5. Add verification queries at end of migration
6. Use IF NOT EXISTS for idempotency per patterns.md
* Patterns to apply:
  * Migration file naming: NNN_description.sql
  * IF NOT EXISTS / IF EXISTS for idempotency
  * CHECK constraints for enum-like columns (lowercase values)
  * Forward-only migrations (no rollback logic)
* Deviations (if any):
  * None

## Unit tests (required)

* Add tests for:
  * Migration SQL syntax is valid (parse test)
  * Table creation is idempotent (can run twice without error)
  * Foreign key constraints reference correct tables
  * CHECK constraint on type column accepts valid values
  * CHECK constraint on type column rejects invalid values
  * Default values are applied correctly
* Suggested locations:
  * tests/unit/migrations/test_029_summary_tables.py
* Mocking/fakes needed:
  * Use in-memory SQLite or mock connection for syntax validation
  * For constraint tests, may need test database connection

## Acceptance criteria (checklist)

* [ ] Migration file created at migrations/029_add_summary_tables.sql
* [ ] summary_nodes table has all specified columns with correct types
* [ ] work_summaries table has CHECK constraint limiting type values
* [ ] work_summaries has UNIQUE constraint on (work_id, type)
* [ ] summarize_settings table has all weight/threshold columns with defaults
* [ ] All foreign keys have ON DELETE CASCADE
* [ ] Indexes created on work_id columns
* [ ] Migration is idempotent (uses IF NOT EXISTS)
* [ ] Verification queries included at end

## Manual verification

* Steps:
  1. Apply migration to test database: `psql -f migrations/029_add_summary_tables.sql`
  2. Verify tables exist: `\dt summary_nodes`, `\dt work_summaries`, `\dt summarize_settings`
  3. Verify constraints: `\d summary_nodes`, `\d work_summaries`
  4. Test CHECK constraint: attempt to insert invalid type value
* Expected results:
  * All three tables created with correct schema
  * Foreign keys and indexes visible in table descriptions
  * Invalid type values rejected by CHECK constraint

## Notes

* Requirements covered: R2 (data model), R4 (settings storage), R10 (derived outputs storage)
* Migration number 029 assumes 028 is the latest; verify before finalizing
* JSONB columns use DEFAULT '[]' to simplify application code
* The type CHECK constraint uses lowercase values per patterns.md enum conventions
* ON DELETE CASCADE ensures summary data is cleaned up when works/chunks are deleted
