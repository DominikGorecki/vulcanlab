# Ticket: work-summarization.T03 - SQLAlchemy Models and init_db Integration

## Source

* Spec: documentation/work/work-summarization.spec.md
* Patterns: documentation/patterns.md

## Goal

* Create SQLAlchemy ORM models for summary_nodes, work_summaries, and summarize_settings tables
* Integrate new models into init_db.py for fresh database installs
* Seed default summarize_settings configuration

## Phase

* Migrations

## Scope

### In scope

* src/vulcanlab/data/models/summary_node.py - SummaryNode model
* src/vulcanlab/data/models/work_summary.py - WorkSummary model
* src/vulcanlab/data/models/summarize_settings.py - SummarizeSettings model
* Enum for WorkSummaryType (abstract, outline, key_concepts, chapter_summaries)
* Update src/vulcanlab/data/models/__init__.py to export new models
* Add table creation to src/vulcanlab/data/schema/specialized_tables.py
* Seed default settings in src/vulcanlab/data/seeding/defaults.py
* Update init_db.py to call new creation/seeding functions

### Out of scope

* API endpoints (T11)
* Core summarization logic (T04-T10)

## Dependencies

* Depends on: T02
* Unblocks: T04, T05, T06, T07, T08, T09, T10, T11

## Implementation plan

1. Create src/vulcanlab/data/models/summarize_settings.py with SummarizeSettings model:
   - All columns matching migration schema
   - Appropriate defaults matching migration
2. Create src/vulcanlab/data/models/summary_node.py with SummaryNode model:
   - All columns with correct types (JSONB as dict/list)
   - Relationships: chunk (FK), work (FK)
   - Use mapped_column with appropriate types
3. Create src/vulcanlab/data/models/work_summary.py with:
   - WorkSummaryType enum (lowercase values per patterns.md)
   - WorkSummary model with type column using the enum
   - Relationship to Work
4. Update src/vulcanlab/data/models/__init__.py to import and export new models
5. Add create_summary_tables() function to src/vulcanlab/data/schema/specialized_tables.py:
   - Create summary_nodes table
   - Create work_summaries table
   - Create summarize_settings table
   - Transfer ownership to app_user
6. Add seed_summarize_settings() function to src/vulcanlab/data/seeding/defaults.py:
   - Insert default row if not exists
7. Update init_db.py init_database() to call create_summary_tables() and seed_summarize_settings()
8. Import new models in init_db.py to ensure they are registered with Base
* Patterns to apply:
  * Enum capitalization: UPPERCASE constant names, lowercase values
  * Database initialization module structure per patterns.md
  * Session management: sessions passed explicitly
  * Docstrings documenting CHECK constraint values
* Deviations (if any):
  * None

## Unit tests (required)

* Add tests for:
  * SummaryNode model can be instantiated with valid data
  * SummaryNode validates required fields
  * WorkSummary model enforces type enum values
  * WorkSummaryType enum values match expected lowercase strings
  * SummarizeSettings defaults are correct
  * Relationships are correctly defined (chunk, work)
* Suggested locations:
  * tests/unit/data/models/test_summary_node.py
  * tests/unit/data/models/test_work_summary.py
  * tests/unit/data/models/test_summarize_settings.py
* Mocking/fakes needed:
  * Mock database session for model instantiation tests

## Acceptance criteria (checklist)

* [ ] SummaryNode model created with all columns from spec
* [ ] WorkSummary model created with type enum and CHECK constraint alignment
* [ ] SummarizeSettings model created with all weight/threshold columns
* [ ] WorkSummaryType enum uses lowercase values matching DB CHECK constraint
* [ ] All models exported from models/__init__.py
* [ ] create_summary_tables() function added to specialized_tables.py
* [ ] seed_summarize_settings() function seeds defaults
* [ ] init_db.py calls new functions in correct order
* [ ] Unit tests pass

## Manual verification

* Steps:
  1. Run `python -m vulcanlab.data.init_db -v` on a fresh database
  2. Verify tables are created: `\dt summary_nodes`, `\dt work_summaries`, `\dt summarize_settings`
  3. Verify default settings seeded: `SELECT * FROM summarize_settings`
  4. Test model import: `from vulcanlab.data.models import SummaryNode, WorkSummary, SummarizeSettings`
* Expected results:
  * Tables created without errors
  * Default settings row exists with expected values
  * Models import successfully

## Notes

* Requirements covered: R2, R4, R10
* JSONB columns in SQLAlchemy should use `mapped_column(JSONB)` or dialect-specific type
* WorkSummaryType enum must document the CHECK constraint values in docstring per patterns.md
* The create_summary_tables function should be idempotent (IF NOT EXISTS pattern)
* Ownership transfer to app_user is required for functions/sequences per patterns.md
