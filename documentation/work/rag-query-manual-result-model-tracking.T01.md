# Ticket: rag-query-manual-result-model-tracking.T01 - Database Schema & Models for Result Model Tracking

## Source

* Spec: documentation/work/rag-query-manual-result-model-tracking.spec.md
* Patterns: documentation/patterns.md

## Goal

* Create `result_models` table to store LLM model names
* Add `model_id` foreign key to `results` table
* Implement SQLAlchemy models for ResultModel and update Result model
* Ensure fresh database installs support the new schema without requiring migrations

## Scope

### In scope

* Migration script `025_add_model_tracking.sql` creating `result_models` table and altering `results` table
* SQLAlchemy `ResultModel` model in new file `src/vulcanlab/data/models/result_model.py`
* Update `Result` model in `src/vulcanlab/data/models/result.py` with `model_id` field and relationship
* Add `create_result_models_table()` function to `src/vulcanlab/data/init_db.py`
* Add `seed_default_result_model()` function to `src/vulcanlab/data/init_db.py`
* Import and call new functions in `init_database()` orchestration
* Seed "Unspecified" default model record
* Unit tests for model CRUD operations

### Out of scope

* API endpoints (covered in T02)
* Frontend changes (covered in T03-T05)
* Model selection logic (covered in T02)
* Results display changes (covered in T04-T05)

## Dependencies

* Depends on: none
* Unblocks: T02, T03, T04, T05

## Implementation plan

1. Create migration script `migrations/025_add_model_tracking.sql`:
   * Create `result_models` table with columns: `id SERIAL PRIMARY KEY`, `name VARCHAR(200) UNIQUE NOT NULL`, `created_at`, `updated_at`
   * Create index on `name` for unique constraint lookups
   * Create trigger function `update_result_models_updated_at()` for auto-updating `updated_at`
   * Create trigger to call the function before UPDATE
   * Alter `results` table to add `model_id INTEGER NULL REFERENCES result_models(id) ON DELETE SET NULL`
   * Create index `ix_results_model_id` on `results(model_id)` for join performance
   * Seed default "Unspecified" model: `INSERT INTO result_models (name) VALUES ('Unspecified') ON CONFLICT (name) DO NOTHING`
   * Grant permissions to app user on `result_models` table and sequence (follow pattern from `009_create_results_table.sql`)

2. Create SQLAlchemy model `src/vulcanlab/data/models/result_model.py`:
   * Define `ResultModel` class extending `Base`
   * Add mapped columns: `id`, `name` (String(200), unique=True), `created_at`, `updated_at`
   * Use `server_default=func.now()` and `onupdate=func.now()` for timestamps
   * Add `__repr__` method for debugging

3. Update `src/vulcanlab/data/models/result.py`:
   * Add `model_id` field: `Mapped[Optional[int]]` with `ForeignKey("result_models.id", ondelete="SET NULL")`, nullable=True, index=True
   * Add relationship: `model: Mapped[Optional["ResultModel"]] = relationship("ResultModel")`
   * Import `Optional` from typing if not already present

4. Update `src/vulcanlab/data/init_db.py`:
   * Import `ResultModel` model in the model imports section (line ~30)
   * Add `create_result_models_table()` function:
     - Create table using raw SQL (mirrors migration) with trigger for `updated_at`
     - Transfer ownership to app user
     - Handle errors gracefully (consistent with other `create_*` functions)
   * Add `seed_default_result_model()` function:
     - Insert "Unspecified" model using raw SQL with `ON CONFLICT DO NOTHING`
     - Use verbose parameter for logging
   * Update `init_database()` function to call both new functions in correct order (after `create_tables()`, before `seed_prompt_templates()`)

5. Update `src/vulcanlab/data/models/__init__.py`:
   * Export `ResultModel` from the models package

6. Write unit tests in `tests/unit/test_result_model_crud.py`:
   * Test creating ResultModel via SQLAlchemy ORM
   * Test unique constraint on model name (expect IntegrityError on duplicate)
   * Test creating Result with model_id (foreign key works)
   * Test querying Result with joined model data (relationship works)
   * Test NULL model_id is allowed
   * Test ON DELETE SET NULL behavior (delete model, verify result.model_id becomes NULL)

* Patterns to apply:
  * **Database ORM**: SQLAlchemy declarative models with typed Mapped columns
  * **Migration Strategy**: SQL-based migration following 001-024 numbering convention
  * **Fresh Install Pattern**: Mirror migration logic in `init_db.py` functions (consistent with `create_enums`, `create_vector_indexes`, etc.)
  * **Seeding Pattern**: Idempotent seed function with `ON CONFLICT DO NOTHING` (consistent with `seed_prompt_templates`)
  * **Session Management**: Tests receive session as parameter (do not create inside test)

* Deviations (if any):
  * None - follows all established patterns

## Unit tests (required)

* Add tests for:
  * Create ResultModel with valid name, verify it persists
  * Create ResultModel with duplicate name, expect unique constraint violation
  * Create Result with model_id, verify foreign key relationship
  * Query Result and join with ResultModel, verify model name is accessible via relationship
  * Create Result with NULL model_id, verify it is allowed
  * Delete ResultModel, verify associated Result.model_id becomes NULL (ON DELETE SET NULL)
  * Update ResultModel.updated_at timestamp is auto-updated on modification

* Suggested locations:
  * `tests/unit/test_result_model_crud.py` - new file for ResultModel CRUD tests
  * May extend `tests/unit/test_result.py` if it exists, or create new file

* Mocking/fakes needed:
  * Mock database session (use pytest fixtures with in-memory SQLite or mock session)
  * Do NOT connect to real database (per patterns.md testing strategy)

## Acceptance criteria (checklist)

* [ ] Migration script `025_add_model_tracking.sql` exists and creates `result_models` table
* [ ] Migration script alters `results` table to add `model_id` column
* [ ] Migration script creates indexes on `result_models.name` and `results.model_id`
* [ ] Migration script seeds "Unspecified" default model
* [ ] Migration script grants permissions to app user
* [ ] SQLAlchemy `ResultModel` class exists in `src/vulcanlab/data/models/result_model.py`
* [ ] `Result` model updated with `model_id` field and relationship to `ResultModel`
* [ ] `ResultModel` exported from `src/vulcanlab/data/models/__init__.py`
* [ ] `create_result_models_table()` function added to `init_db.py`
* [ ] `seed_default_result_model()` function added to `init_db.py`
* [ ] `init_database()` calls both new functions in correct order
* [ ] Unit tests cover ResultModel CRUD operations
* [ ] Unit tests verify unique constraint on model name
* [ ] Unit tests verify foreign key relationship between Result and ResultModel
* [ ] Unit tests verify NULL model_id is allowed
* [ ] Unit tests verify ON DELETE SET NULL behavior
* [ ] All unit tests pass without connecting to real database

## Manual verification

* Steps:
  1. Run migration on development database: `psql -U <admin_user> -d <db_name> -f migrations/025_add_model_tracking.sql`
  2. Verify `result_models` table exists: `\d result_models`
  3. Verify `results.model_id` column exists: `\d results`
  4. Verify "Unspecified" model seeded: `SELECT * FROM result_models;`
  5. Run fresh database init: `python -m vulcanlab.data.init_db -v`
  6. Verify `result_models` table created without errors
  7. Verify "Unspecified" model exists in fresh install
  8. Run unit tests: `pytest tests/unit/test_result_model_crud.py -v`

* Expected results:
  * Migration runs successfully with no errors
  * `result_models` table has correct schema (id, name, created_at, updated_at)
  * `results.model_id` is a nullable foreign key to `result_models.id`
  * Indexes created on both tables
  * "Unspecified" model exists with id=1
  * Fresh install creates all objects without requiring migration
  * All unit tests pass

## Notes

* Requirements covered: R11, R12, R13, R14, R15
* Migration script should follow permissions pattern from `009_create_results_table.sql` (grant to app user)
* Use `VARCHAR(200)` for model name to accommodate long model identifiers like "claude-3-opus-20240229"
* Trigger for `updated_at` should follow pattern from other tables (e.g., `io_files`, `prompt_meta`)
* "Unspecified" model should ideally have id=1 for test predictability (first insert gets id=1 in SERIAL)
* ON DELETE SET NULL ensures referential integrity without breaking existing results if a model is deleted
* Fresh install pattern: `create_result_models_table()` should mirror the migration SQL, not rely on SQLAlchemy `create_all()` alone (consistent with other explicit table creation functions)
