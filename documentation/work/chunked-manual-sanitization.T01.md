# Ticket: chunked-manual-sanitization.T01 - Database Schema and Template Foundation

## Source

* Spec: documentation/work/chunked-manual-sanitization.spec.md
* Patterns: documentation/patterns.md

## Goal

* Create database table `batch_sanitization_progress` to track batched sanitization state.
* Create and seed new prompt template `simple_sanitize_large_batched` for batched workflows.
* Add new configuration keys to `vulcanlab.config.json` for batch size settings.

## Scope

### In scope

* SQL migration script to create `batch_sanitization_progress` table with all required columns and indexes.
* New template file `simple_sanitize_large_batched.txt` based on existing `simple_sanitize_large.txt` with context section.
* Template metadata entry in `templates.yaml`.
* Configuration schema update in `vulcanlab.config.json` with `batch_size_headings` and `batch_context_headings`.
* Unit tests for template seeding validation.

### Out of scope

* Core batching logic functions (T02).
* API endpoints (T03).
* UI changes (T04, T05, T06).
* Actual usage of the table or template (handled in subsequent tickets).

## Dependencies

* Depends on: None (foundation ticket)
* Unblocks: T02, T03

## Implementation plan

* Create migration script `migrations/0XX_batch_sanitization_progress.sql`:
  * Define table with columns: id, work_id, total_batches, current_batch_index, batch_sizes (JSONB), batch_results (JSONB), batch_context (JSONB), created_at, updated_at.
  * Add UNIQUE constraint on work_id.
  * Create index on work_id for fast lookups.
  * Add foreign key constraint to works table with ON DELETE CASCADE.
* Read existing `src/vulcanlab/data/seed_data/templates/simple_sanitize_large.txt`.
* Create new `src/vulcanlab/data/seed_data/templates/simple_sanitize_large_batched.txt`:
  * Copy base content from `simple_sanitize_large.txt`.
  * Add section for hierarchical context headings before condensed document input.
  * Add template variables: `{condensed_document}`, `{context_headings}`, `{batch_range}`.
  * Clearly indicate batch processing in instructions (e.g., "You are processing headings {batch_range} of the document").
* Update `src/vulcanlab/data/seed_data/templates.yaml`:
  * Add entry with function_tag: `simple_sanitize_large_batched`, version: 1, title: "Simple Conversion - Large Document Batched Sanitization".
* Update `vulcanlab.config.json` under `conversion` section:
  * Add `"batch_size_headings": 5000`.
  * Add `"batch_context_headings": 25`.
* Patterns to apply:
  * **Database Migrations** - SQL-based migration following existing pattern in `migrations/`.
  * **Prompt Template Seeding** - YAML + .txt file pattern as per patterns.md.
  * **Configuration** - JSON-based app config in `vulcanlab.config.json`.
* Deviations (if any):
  * None; follows established patterns.

## Unit tests (required)

* Add tests for:
  * Template YAML validation: Verify `simple_sanitize_large_batched` entry parses correctly from `templates.yaml`.
  * Template file existence: Verify `simple_sanitize_large_batched.txt` file exists and is non-empty.
  * Template variable presence: Verify template contains required variables (`{condensed_document}`, `{context_headings}`, `{batch_range}`).
  * Config schema validation: Verify `batch_size_headings` and `batch_context_headings` load correctly from config.
* Suggested locations:
  * `tests/unit/test_batch_sanitization_template.py`
  * `tests/unit/test_batch_config.py`
* Mocking/fakes needed:
  * Mock file system for template reading in tests.
  * No database mocking needed for this ticket (schema only, no logic).

## Acceptance criteria (checklist)

* [ ] Migration script `0XX_batch_sanitization_progress.sql` created with correct table schema.
* [ ] Table includes all required columns: id, work_id, total_batches, current_batch_index, batch_sizes, batch_results, batch_context, created_at, updated_at.
* [ ] UNIQUE constraint on work_id and index on work_id created.
* [ ] Foreign key to works table with ON DELETE CASCADE added.
* [ ] Template file `simple_sanitize_large_batched.txt` created with context section.
* [ ] Template includes variables: `{condensed_document}`, `{context_headings}`, `{batch_range}`.
* [ ] Entry added to `templates.yaml` with correct metadata.
* [ ] `vulcanlab.config.json` updated with `batch_size_headings: 5000` and `batch_context_headings: 25`.
* [ ] Template seeds successfully via `python -m vulcanlab.data.init_db -v`.
* [ ] All unit tests pass.

## Manual verification

* Steps:
  * Run migration script: `psql -U postgres -d psych_rag_test -f migrations/0XX_batch_sanitization_progress.sql`.
  * Verify table exists: `\d batch_sanitization_progress` in psql.
  * Verify indexes: `\di batch_sanitization_progress*`.
  * Run template seeding: `python -m vulcanlab.data.init_db -v`.
  * Query database: `SELECT * FROM prompt_templates WHERE function_tag = 'simple_sanitize_large_batched';`.
  * Load config: `python -c "from vulcanlab.config import load_config; print(load_config()['conversion'])"`.
* Expected results:
  * Table `batch_sanitization_progress` exists with all columns and constraints.
  * Index `idx_batch_sanitization_progress_work_id` exists.
  * Template record inserted with function_tag `simple_sanitize_large_batched`.
  * Config shows `batch_size_headings: 5000` and `batch_context_headings: 25`.

## Notes

* Requirements covered: R4 (partial - table creation), R9 (template seeding), R10 (partial - config schema).
* Migration number should follow existing sequence in `migrations/` directory.
* Template content should be clear about batch processing to avoid user confusion.
* Ensure template file uses proper escaping for JSON output examples (double braces for literal braces in prompt).
