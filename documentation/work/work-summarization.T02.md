# Ticket: work-summarization.T02 - SQLAlchemy Models and Schema Module Updates

## Source

* Spec: documentation/work/work-summarization.spec.md
* Patterns: documentation/patterns.md

## Goal

* Create SQLAlchemy ORM models for `SummaryChunk`, `SummaryResult`, and `SummarizeSettings`
* Update `src/vulcanlab/data/schema/specialized_tables.py` to create tables via init_db
* Register models in `src/vulcanlab/data/models/__init__.py`
* Seed default settings row on database initialization

## Phase

* Migrations

## Scope

### In scope

* SQLAlchemy model classes in `src/vulcanlab/data/models/`
* Schema creation functions in `src/vulcanlab/data/schema/specialized_tables.py`
* Model registration in `__init__.py`
* Default settings seeding in `src/vulcanlab/data/seeding/defaults.py`
* Update `init_db.py` to call new schema/seeding functions

### Out of scope

* The SQL migration file (T01)
* Prompt template creation (T03)
* Core module implementation (T04+)

## Dependencies

* Depends on: T01 (migration defines schema)
* Unblocks: T04, T05, T06, T07, T08, T09, T10, T11

## Implementation plan

1. Create `src/vulcanlab/data/models/summary_chunk.py`:
   - Class `SummaryChunk(Base)` with `__tablename__ = "summary_chunks"`
   - All columns from migration with proper types (Integer, Float, DateTime)
   - Relationships: `work`, `heading_chunk`, `content_chunk`
2. Create `src/vulcanlab/data/models/summary_result.py`:
   - Class `SummaryResult(Base)` with `__tablename__ = "summary_results"`
   - All columns from migration
   - Relationships: `work`, `chunk` (the heading-chunk)
3. Create `src/vulcanlab/data/models/summarize_settings.py`:
   - Class `SummarizeSettings(Base)` with `__tablename__ = "summarize_settings"`
   - All settings columns with defaults matching migration
4. Update `src/vulcanlab/data/models/__init__.py`:
   - Import and export all three new models
5. Update `src/vulcanlab/data/schema/specialized_tables.py`:
   - Add `create_summarization_tables(conn, app_user, verbose)` function
   - Mirror the SQL from migration for fresh installs
   - Transfer ownership to app_user
6. Update `src/vulcanlab/data/seeding/defaults.py`:
   - Add `seed_summarize_settings(session, verbose)` function
   - Insert default row if table is empty
7. Update `src/vulcanlab/data/init_db.py`:
   - Call `create_summarization_tables()` in appropriate order
   - Call `seed_summarize_settings()` after table creation

* Patterns to apply:
  * **ORM Models** - Use SQLAlchemy declarative models in `data/models/`
  * **Session Management** - Models define relationships, session passed to operations
  * **Migration + init_db sync** - Schema module mirrors migration for fresh installs
  * **Database Init Module Structure** - Follow existing modular organization
* Deviations (if any):
  * None

## Unit tests (required)

* Add tests for:
  * `SummaryChunk` model can be instantiated with valid data
  * `SummaryResult` model can be instantiated with valid data
  * `SummarizeSettings` model has correct default values
  * Relationships resolve correctly (mock session)
  * `seed_summarize_settings` creates row when table empty, skips when exists
* Suggested locations:
  * `tests/unit/test_summary_models.py`
  * `tests/unit/test_summarize_settings_seeding.py`
* Mocking/fakes needed:
  * Mock SQLAlchemy session for model tests
  * Mock database connection for seeding tests

## Acceptance criteria (checklist)

* [ ] Three model files created in `src/vulcanlab/data/models/`
* [ ] Models exported from `__init__.py`
* [ ] Schema creation function added to `specialized_tables.py`
* [ ] Seeding function added to `defaults.py`
* [ ] `init_db.py` calls new functions in correct order
* [ ] Running `python -m vulcanlab.data.init_db -v` creates tables and seeds settings
* [ ] Unit tests pass for all models

## Manual verification

* Steps:
  * Drop and recreate database using `init_db.py`
  * Query `summarize_settings` table to verify default row exists
  * Use Python REPL to import models and verify they load without errors
  * Create a `SummaryChunk` instance in REPL with mock data
* Expected results:
  * Tables created via init_db match migration schema
  * Default settings row has expected values
  * Models import and instantiate correctly

## Notes

* Requirements covered: R5, R9, Settings storage (data layer foundation)
* Follow existing model patterns from `src/vulcanlab/data/models/chunk.py`
* Use `Mapped` type hints and `mapped_column` per existing conventions
* Ensure relationship back_populates are consistent with Work and Chunk models
