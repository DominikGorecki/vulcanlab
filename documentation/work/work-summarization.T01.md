# Ticket: work-summarization.T01 - Database Migration for Summary Tables

## Source

* Spec: documentation/work/work-summarization.spec.md
* Patterns: documentation/patterns.md

## Goal

* Create SQL migration for `summary_chunks`, `summary_results`, and `summarize_settings` tables
* Establish foreign key relationships to `works` and `chunks` tables
* Add appropriate indexes for query performance

## Phase

* Migrations

## Scope

### In scope

* SQL migration file `migrations/030_add_summarization_tables.sql`
* Three new tables: `summary_chunks`, `summary_results`, `summarize_settings`
* Foreign keys, indexes, and constraints as specified
* Timestamp trigger for `summarize_settings.updated_at`
* Verification queries

### Out of scope

* SQLAlchemy models (T02)
* Seeding default settings values (T02)
* init_db.py updates (T02)

## Dependencies

* Depends on: none
* Unblocks: T02, T03, T04, T05, T06, T07, T08, T09

## Implementation plan

1. Create `migrations/030_add_summarization_tables.sql`
2. Add `summarize_settings` table with columns:
   - id (SERIAL PRIMARY KEY)
   - min_heading_word_count (INTEGER DEFAULT 500)
   - max_total_heading_words (INTEGER DEFAULT 2500)
   - dense_top_k (INTEGER DEFAULT 7)
   - lexical_top_k (INTEGER DEFAULT 7)
   - rrf_k (INTEGER DEFAULT 60)
   - rrf_top_k (INTEGER DEFAULT 7)
   - mmr_lambda (FLOAT DEFAULT 0.7)
   - mmr_top_n (INTEGER DEFAULT 5)
   - max_llm_calls (INTEGER DEFAULT 5)
   - max_tokens_per_call (INTEGER DEFAULT 15000)
   - tokens_per_word (FLOAT DEFAULT 0.75)
   - h1_h2_min_chunks (INTEGER DEFAULT 2)
   - h3_min_chunks (INTEGER DEFAULT 1)
   - created_at, updated_at (TIMESTAMP WITH TIME ZONE)
3. Add `summary_chunks` table with columns:
   - id (SERIAL PRIMARY KEY)
   - work_id (INTEGER FK works.id ON DELETE CASCADE)
   - heading_chunk_id (INTEGER FK chunks.id ON DELETE CASCADE)
   - content_chunk_id (INTEGER FK chunks.id ON DELETE CASCADE)
   - word_count (INTEGER NOT NULL)
   - dense_score (FLOAT)
   - lexical_score (FLOAT)
   - rrf_score (FLOAT)
   - mmr_score (FLOAT)
   - rank_position (INTEGER NOT NULL)
   - created_at (TIMESTAMP WITH TIME ZONE DEFAULT NOW())
4. Add `summary_results` table with columns:
   - id (SERIAL PRIMARY KEY)
   - work_id (INTEGER FK works.id ON DELETE CASCADE)
   - chunk_id (INTEGER FK chunks.id ON DELETE CASCADE, UNIQUE)
   - summary_content (TEXT NOT NULL)
   - prompt_index (INTEGER)
   - created_at, updated_at (TIMESTAMP WITH TIME ZONE)
5. Create indexes: `(work_id)` on both tables, `(heading_chunk_id)`, `(heading_chunk_id, rank_position)` on summary_chunks, `(chunk_id)` UNIQUE on summary_results
6. Create trigger function and trigger for `summarize_settings.updated_at`
7. Add table comments
8. Add verification queries at end of migration

* Patterns to apply:
  * **Migration Patterns** - Use IF NOT EXISTS for idempotency, include verification queries
  * **Dual-Track Migration** - Migration file will be replicated in init_db schema modules (T02)
* Deviations (if any):
  * None

## Unit tests (required)

* Add tests for:
  * Migration file exists and is valid SQL (syntax check)
  * Tables created with correct columns and types
  * Foreign key constraints work (insert/delete cascade)
  * Indexes exist after migration
  * Trigger updates `updated_at` on summarize_settings modification
* Suggested locations:
  * `tests/unit/test_migration_030.py`
* Mocking/fakes needed:
  * Test database connection (use test DB, not production)

## Acceptance criteria (checklist)

* [ ] Migration file `030_add_summarization_tables.sql` exists in `migrations/`
* [ ] All three tables created with correct schema
* [ ] Foreign keys cascade on delete
* [ ] Indexes created for performance-critical queries
* [ ] Trigger auto-updates `updated_at` on settings changes
* [ ] Migration is idempotent (can run multiple times safely)

## Manual verification

* Steps:
  * Run `psql -f migrations/030_add_summarization_tables.sql` against test database
  * Query `information_schema.tables` to verify tables exist
  * Insert test row into `summarize_settings`, update it, verify `updated_at` changes
  * Insert rows into `summary_chunks` and `summary_results` with valid FKs
  * Delete a work and verify cascade deletes related rows
* Expected results:
  * All tables created without errors
  * Constraints enforced correctly
  * Cascade deletes work as expected

## Notes

* Requirements covered: R5 (summary_chunks storage), R9 (summary_results storage), Settings storage
* Next migration number is 030 (029 exists but is being replaced/ignored)
* Ensure column types match what SQLAlchemy models will expect in T02
