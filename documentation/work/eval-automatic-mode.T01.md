# Ticket: eval-automatic-mode.T01 - Database Schema and Migration for Automatic Mode

## Source

* Spec: documentation/work/eval-automatic-mode.spec.md
* Patterns: documentation/patterns.md

## Goal

* Add database columns to support automatic evaluation mode configuration
* Create migration file and update init_db.py for fresh installs
* Enable experiments to store auto mode settings and prompts to be grouped

## Scope

### In scope

* Add auto_mode_enabled, auto_answer_provider, auto_judge_provider columns to experiments table
* Add prompt_group_id column to experiment_prompts table
* Create migration file 016_add_auto_eval_mode.sql
* Update init_db.py to create new columns for fresh installs
* Add database constraint: if auto_mode_enabled is true, both provider fields must be non-null
* Add index on (experiment_id, prompt_group_id) for efficient grouped prompt queries

### Out of scope

* API endpoints or business logic
* UI components
* Data migration or backfill for existing experiments (defaults handle this)
* LLM factory changes

## Dependencies

* Depends on: none
* Unblocks: T02, T03, T04, T05

## Implementation plan

1. Create migration file migrations/016_add_auto_eval_mode.sql:
   * Add auto_mode_enabled BOOLEAN NOT NULL DEFAULT FALSE to experiments
   * Add auto_answer_provider VARCHAR(50) NULL to experiments
   * Add auto_judge_provider VARCHAR(50) NULL to experiments
   * Add CHECK constraint: if auto_mode_enabled = true, both provider fields must not be null
   * Add prompt_group_id INTEGER NULL to experiment_prompts
   * Create index on (experiment_id, prompt_group_id) in experiment_prompts
2. Update src/vulcanlab/data/models/experiment.py:
   * Add auto_mode_enabled, auto_answer_provider, auto_judge_provider fields to Experiment model
   * Add prompt_group_id field to ExperimentPrompt model
3. Update src/vulcanlab/data/init_db.py:
   * Modify experiments table creation to include auto mode columns and constraint
   * Modify experiment_prompts table creation to include prompt_group_id and index
   * Ensure fresh installs do not need migration
4. Test migration on dev database:
   * Run migration script manually
   * Verify columns and constraints created correctly
   * Verify default values work for existing experiments
5. Patterns to apply:
   * Database patterns - SQLAlchemy declarative models with explicit column definitions
   * Migration pattern - SQL-based migrations with idempotent operations
* Deviations (if any):
   * None

## Unit tests (required)

* Add tests for:
   * Experiment model accepts auto mode fields with valid values
   * Experiment model validation: auto_mode_enabled=true requires both provider fields non-null
   * ExperimentPrompt model accepts prompt_group_id field
   * Database constraint prevents saving auto_mode_enabled=true with null providers
* Suggested locations:
   * tests/unit/test_experiment_model.py (create if not exists)
   * tests/unit/test_migration_016.py (create)
* Mocking/fakes needed:
   * Mock database session for model tests
   * Use in-memory SQLite or pytest fixtures for constraint testing

## Acceptance criteria (checklist)

* [ ] Migration file 016_add_auto_eval_mode.sql created
* [ ] Migration adds auto_mode_enabled, auto_answer_provider, auto_judge_provider to experiments
* [ ] Migration adds prompt_group_id to experiment_prompts
* [ ] Migration creates CHECK constraint for auto mode validation
* [ ] Migration creates index on (experiment_id, prompt_group_id)
* [ ] Experiment model updated with new fields
* [ ] ExperimentPrompt model updated with prompt_group_id
* [ ] init_db.py updated to create columns for fresh installs
* [ ] Unit tests pass for model validation
* [ ] Migration runs successfully on dev database
* [ ] Existing experiments default to auto_mode_enabled=false

## Manual verification

* Steps:
  1. Run migration on dev database: `python -m vulcanlab.data.run_migration 016`
  2. Connect to database and verify columns exist: `\d experiments` and `\d experiment_prompts`
  3. Insert test experiment with auto_mode_enabled=true and both providers set
  4. Try to insert experiment with auto_mode_enabled=true and null provider (should fail)
  5. Query existing experiments and verify auto_mode_enabled=false by default
  6. Run init_db.py on fresh test database and verify columns created
* Expected results:
  * All columns created successfully
  * Constraint prevents invalid auto mode configurations
  * Existing experiments unaffected (default to manual mode)
  * Fresh installs have all columns without needing migration

## Notes

* Requirements covered: R1, R2, R16
* prompt_group_id is scoped to experiment_id (not globally unique)
* Generated as max(prompt_group_id) + 1 per experiment in application logic (not database)
* Default FALSE for auto_mode_enabled ensures backwards compatibility
* NULL providers allowed when auto_mode_enabled=false
