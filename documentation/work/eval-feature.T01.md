# Ticket: eval-feature.T01 - Database Schema and Models

## Source

* Spec: documentation/work/eval-feature.spec.md
* Patterns: documentation/patterns.md

## Goal

* Create complete database schema for eval feature with 6 new tables
* Implement SQLAlchemy models following existing patterns
* Provide migration script with proper cascade constraints and indexes

## Scope

### In scope

* Tables: experiments, experiment_dimensions, experiment_prompts, experiment_answers, experiment_evaluations, experiment_dimension_results
* SQLAlchemy declarative models in src/vulcanlab/data/models/
* Database migration script with CASCADE constraints
* Foreign key relationships with proper ON DELETE CASCADE
* Check constraints for score ranges (-10 to 10)
* Indexes on foreign key columns
* Model __init__.py exports

### Out of scope

* API endpoints or business logic
* UI components
* Template table modifications (defer to T06)
* Data seeding or fixtures
* Integration tests

## Dependencies

* Depends on: none (foundation ticket)
* Unblocks: T02, T03, T04, T05, T06

## Implementation plan

1. Create new model file: src/vulcanlab/data/models/experiment.py
2. Define Experiment model class with all fields from spec (id, name, description_x, description_y, model_x, model_y, judge_model, eval_template_id, created_at, updated_at)
3. Define ExperimentDimension model with FK to experiments, unique constraint on (experiment_id, dimension_name)
4. Define ExperimentPrompt model with FK to experiments
5. Define ExperimentAnswer model with FK to experiment_prompts, include is_x_mapped_to_a boolean
6. Define ExperimentEvaluation model with FK to experiment_answers, CHECK constraint on overall_score, unique constraint on answer_id
7. Define ExperimentDimensionResult model with FK to experiment_evaluations, CHECK constraint on score
8. Add indexes to all FK columns using SQLAlchemy Index()
9. Export all models in src/vulcanlab/data/models/__init__.py
10. Create migration script in migrations/ folder following existing migration patterns
11. Add migration SQL for CREATE TABLE statements with all constraints
12. Test migration script applies cleanly on empty test database
13. Patterns to apply:
    * **ORM declarative models**: Follow existing model patterns in src/vulcanlab/data/models/
    * **Database migrations**: Follow existing migration script structure
    * **Naming conventions**: snake_case for tables and columns, PascalCase for model classes

## Unit tests (required)

* Add tests for:
  * Model instantiation with valid data
  * Model relationships (FK integrity, cascade behavior with mocked session)
  * Check constraints reject invalid scores (< -10 or > 10)
  * Unique constraints on (experiment_id, dimension_name) and (answer_id) enforced
  * Timestamp fields auto-populate on creation
  * CASCADE delete behavior (mock delete experiment, verify prompts would cascade)
* Suggested locations:
  * tests/unit/test_experiment_models.py
* Mocking/fakes needed:
  * Mock SQLAlchemy session using unittest.mock or pytest fixtures
  * Mock UUID generation for deterministic IDs in tests
  * Do NOT connect to real database

## Acceptance criteria (checklist)

* [ ] All 6 tables defined as SQLAlchemy models
* [ ] Foreign key relationships with ON DELETE CASCADE configured
* [ ] Check constraints on overall_score and dimension result scores (-10 to 10)
* [ ] Unique constraints on (experiment_id, dimension_name) and (answer_id)
* [ ] Indexes created on all FK columns
* [ ] Models exported in __init__.py
* [ ] Migration script creates all tables successfully
* [ ] Unit tests achieve >80% coverage for model definitions
* [ ] All tests pass with mocked DB session (no real DB)

## Manual verification

* Steps:
  1. Run migration script on local dev database
  2. Use psql or DB tool to verify all 6 tables exist
  3. Check table schemas match spec (column types, constraints, indexes)
  4. Attempt to insert test data violating constraints (should fail)
  5. Test cascade delete by inserting experiment → prompt → answer → eval, then delete experiment
* Expected results:
  * All tables present with correct schema
  * Constraints enforced (scores reject <-10 or >10, unique constraints work)
  * Cascade deletes propagate correctly
  * Indexes exist on FK columns

## Notes

* Requirements covered: Foundation for R1-R15 (data layer)
* Use UUID for all primary keys (consistent with existing models if applicable, otherwise use auto-incrementing integers)
* Check existing migration pattern: if using Alembic, follow Alembic conventions; if using raw SQL scripts, follow that pattern
* The eval_template_id FK should be nullable initially (T06 will integrate with templates table)
* Default dimensions (factual_correctness, completeness, coherence, hallucination_risk, academic_response) will be handled in application logic, not as database defaults
* Verify timestamp fields use server-side defaults (CURRENT_TIMESTAMP) or application-side (datetime.utcnow)
