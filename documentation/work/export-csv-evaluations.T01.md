# Ticket: export-csv-evaluations.T01 - Core Logic: Evaluation Data Retrieval and Grouping

## Source

* Spec: documentation/work/export-csv-evaluations.spec.md
* Patterns: documentation/patterns.md

## Goal

* Implement the business logic for retrieving all completed evaluations for a specific experiment.
* Calculate stable `grouping_id` values based on the prompt's creation timestamp.
* Prepare the data structure required for CSV generation.

## Scope

### In scope

* Backend: New helper function in `src/vulcanlab/eval/evaluations.py` to fetch evaluation data.
* Logic: Grouping prompts by creation time to assign sequential `grouping_id` (1, 2, 3...).
* Logic: Joining `ExperimentEvaluation`, `ExperimentAnswer`, and `ExperimentPrompt`.
* Logic: Filtering for completed evaluations only.

### Out of scope

* CSV formatting or sanitization (handled in T02).
* API endpoint implementation (handled in T03).

## Dependencies

* Depends on: none
* Unblocks: export-csv-evaluations.T02

## Implementation plan

* Define a internal helper or the start of `export_experiment_evaluations_to_csv` in `src/vulcanlab/eval/evaluations.py`.
* Query all `ExperimentPrompt` records for the experiment, ordered by `created_at` ASC.
* Create a mapping of `prompt_id` to `grouping_id` (index + 1).
* Query all `ExperimentEvaluation` records joined with their answers and prompts for the experiment.
* Structure the retrieved data into a list of dictionaries containing raw fields and the assigned `grouping_id`.
* Patterns to apply:
    * Core Module Logic - Keeping database queries and grouping logic in the core module.

## Unit tests (required)

* Add tests for:
    * Sequential `grouping_id` assignment for multiple prompts.
    * Correct filtering of only completed evaluations.
    * Stability of `grouping_id` across multiple calls (based on timestamp).
* Suggested locations:
    * `tests/unit/test_eval_export_logic.py`
* Mocking/fakes needed:
    * Mock SQLAlchemy session and model instances.

## Acceptance criteria (checklist)

* [ ] `grouping_id` is correctly assigned starting from 1 for the oldest prompt.
* [ ] Only evaluations associated with the target experiment are retrieved.
* [ ] Evaluations for the same prompt share the same `grouping_id`.
* [ ] Prompts without evaluations are correctly excluded from the result.

## Manual verification

* Steps:
    * This ticket is internal logic; manual verification will be performed after T03 is implemented.
    * Verify via unit tests.
* Expected results:
    * Unit tests pass with correct grouping and filtering logic.

## Notes

* Requirements covered: R2, R3
* Assumption: `ExperimentPrompt.created_at` is unique enough or ID order is an acceptable fallback if timestamps match.

