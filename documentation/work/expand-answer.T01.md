# Ticket: expand-answer.T01 - Database Models and Schema

## Source

* Spec: documentation/work/expand-answer.spec.md
* Patterns: documentation/patterns.md

## Goal

* Create SQLAlchemy models for `AnswerExpansion` and `ExpansionSection` with proper enums
* Add idempotent schema creation in `specialized_tables.py`
* Enable database foundation for the entire expansion feature

## Scope

### In scope

* Python enum classes for expansion status and section status
* SQLAlchemy models: `AnswerExpansion`, `ExpansionSection`
* Foreign key relationships to existing `Result` and `Query` models
* Schema DDL in `specialized_tables.py` with `CREATE TABLE IF NOT EXISTS`
* Indexes on `result_id`, `status`, `expansion_id`
* Import new models in `init_db.py`

### Out of scope

* API endpoints (T03)
* Core business logic (T02)
* UI components (T04, T05)
* Data migrations or backfills (not needed for new tables)

## Dependencies

* Depends on: none
* Unblocks: T02, T03, T04, T05, T06

## Implementation plan

1. Create `src/vulcanlab/data/models/expansion.py` with:
   - `ExpansionStatus` enum (created, breakdown_pending, breakdown_complete, sections_in_progress, combining, completed, failed)
   - `SectionStatus` enum (pending, expanding, ready, generating, completed, failed)
   - `AnswerExpansion` model with columns per spec
   - `ExpansionSection` model with columns per spec
   - Relationships: `AnswerExpansion.sections`, `ExpansionSection.expansion`
2. Add model import to `src/vulcanlab/data/models/__init__.py`
3. Add schema creation to `src/vulcanlab/data/schema/specialized_tables.py`:
   - `CREATE TABLE IF NOT EXISTS answer_expansions` with CHECK constraints
   - `CREATE TABLE IF NOT EXISTS expansion_sections` with CHECK constraints
   - `CREATE INDEX IF NOT EXISTS` for specified indexes
4. Register models in `src/vulcanlab/data/init_db.py` imports
5. Write unit tests for model instantiation and enum value mapping

* Patterns to apply:
  * Enum Value Capitalization - Python constants UPPERCASE, values lowercase to match DB CHECK constraints
  * Database Initialization - Use idempotent SQL patterns in specialized_tables.py
  * Session Management - Models designed to work with passed sessions

* Deviations (if any):
  * None

## Unit tests (required)

* Add tests for:
  * `AnswerExpansion` model instantiation with valid enum values
  * `ExpansionSection` model instantiation with valid enum values
  * Enum value strings match expected lowercase format
  * Relationship between AnswerExpansion and ExpansionSection (mocked session)

* Suggested locations:
  * `tests/unit/data/models/test_expansion_models.py`

* Mocking/fakes needed:
  * Mock SQLAlchemy session for relationship testing

## Acceptance criteria (checklist)

* [ ] `ExpansionStatus` and `SectionStatus` enums exist with correct lowercase values
* [ ] `AnswerExpansion` model has all columns from spec (result_id, query_id, mode, status, combined_report, expansion_metadata, timestamps)
* [ ] `ExpansionSection` model has all columns from spec (expansion_id, order, heading, summary, expansion_prompt, RAG fields, status, error_message, timestamps)
* [ ] `answer_expansions.result_id` has UNIQUE constraint (one expansion per result)
* [ ] Schema DDL added to `specialized_tables.py` with idempotent patterns
* [ ] Running `python -m vulcanlab.data.init_db -v` creates tables without error
* [ ] Unit tests pass

## Manual verification

* Steps:
  1. Run `python -m vulcanlab.data.init_db -v`
  2. Connect to PostgreSQL and verify tables exist: `\d answer_expansions` and `\d expansion_sections`
  3. Verify CHECK constraints: `\d+ answer_expansions`
  4. Verify indexes exist: `\di *expansion*`

* Expected results:
  * Tables `answer_expansions` and `expansion_sections` created
  * CHECK constraints enforce valid status values
  * Foreign keys to `results` and `queries` tables
  * Indexes on `result_id`, `status`, `expansion_id` present

## Notes

* Requirements covered: R13 (expansion data separate from queries table), data model requirements from spec
* Enum values MUST be lowercase to match database CHECK constraints per patterns.md
* The `query_id` column is denormalized for convenience in generating original answer URLs
* UNIQUE constraint on `result_id` enforces one expansion per result
