# Ticket: export-jsonl-answers.T01 - Core JSONL Export Logic

## Source

* Spec: documentation/work/export-jsonl-answers.spec.md
* Patterns: documentation/patterns.md

## Goal

* Implement the core business logic to export answer pairs with completed evaluations to JSONL format.
* Ensure the function uses a generator pattern for memory-efficient streaming.
* Include comprehensive unit tests with mocked database sessions.

## Scope

### In scope

* Core function `export_experiment_answers_to_jsonl` in `src/vulcanlab/eval/evaluations.py`.
* Query logic to fetch answer pairs with completed evaluations, joined with prompts.
* Generator pattern yielding one JSONL line per answer pair.
* Proper JSON encoding with Unicode support and special character escaping.
* Unit tests with mocked SQLAlchemy sessions.

### Out of scope

* API endpoint implementation (T02).
* Frontend UI changes (T03).
* Integration tests or real database connections.

## Dependencies

* Depends on: None (uses existing models and database patterns)
* Unblocks: T02

## Implementation plan

* Read existing `export_experiment_evaluations_to_csv` function in `src/vulcanlab/eval/evaluations.py` to understand the query pattern for completed evaluations.
* Create `export_experiment_answers_to_jsonl(session: Session, experiment_id: int)` function in the same file.
* Query `ExperimentAnswer` joined with `ExperimentPrompt` where `ExperimentEvaluation` exists (completed evaluations).
* Use SQLAlchemy's `join()` and `exists()` or `join()` to filter for answers with evaluations.
* For each result, construct a dictionary: `{"prompt_text": ..., "answer_x": ..., "answer_y": ...}`.
* Use `json.dumps(record, ensure_ascii=False)` to serialize each record.
* Yield each JSON line followed by `\n` (generator pattern).
* Add logging to track the export event and record count.
* Patterns to apply:
    * Core Module Logic - All business logic in `src/vulcanlab`, framework-agnostic.
    * Database Patterns - Session passed as argument, SQLAlchemy ORM queries.
    * Testing Strategy - Unit tests with mocked sessions, no real DB connections.
* Deviations (if any):
    * None.

## Unit tests (required)

* Add tests for:
    * Basic export: 2-3 answer pairs with completed evaluations, verify JSONL format.
    * Filtering: Answer pairs without evaluations are excluded.
    * Special characters: Prompts and answers containing quotes, newlines, Unicode characters are properly escaped.
    * Empty experiment: Experiment with no completed evaluations returns empty generator.
    * Invalid experiment ID: Gracefully handle non-existent experiment.
    * JSONL validity: Each line is valid JSON (parseable with `json.loads`).
* Suggested locations:
    * `tests/unit/test_jsonl_export.py` (new file) or add to existing `tests/unit/test_evaluations.py` if it exists.
* Mocking/fakes needed:
    * Mock SQLAlchemy `Session` object.
    * Mock query results with sample `ExperimentAnswer`, `ExperimentPrompt`, and `ExperimentEvaluation` objects.

## Acceptance criteria (checklist)

* [ ] Function `export_experiment_answers_to_jsonl` exists in `src/vulcanlab/eval/evaluations.py`.
* [ ] Function uses generator pattern (yields lines, does not return full string).
* [ ] Each yielded line is valid JSONL: `{...}\n`.
* [ ] Only answer pairs with completed evaluations are included.
* [ ] Each record contains `prompt_text`, `answer_x`, `answer_y` fields.
* [ ] Special characters, newlines, and Unicode are properly escaped.
* [ ] Unit tests cover basic export, filtering, special characters, and empty cases.
* [ ] All unit tests pass with mocked database sessions.

## Manual verification

* Steps:
    * Run unit tests: `pytest tests/unit/test_jsonl_export.py -v`.
    * Inspect test output to verify JSONL formatting.
    * Use a Python REPL to manually call the function with a mocked session and verify generator output.
* Expected results:
    * All unit tests pass.
    * Generated JSONL lines are valid JSON objects.
    * Special characters are correctly escaped.

## Notes

* Requirements covered: R1, R2, R3, R7, R8.
* Follow the same query pattern as `export_experiment_evaluations_to_csv` for consistency.
* Use `json.dumps(ensure_ascii=False)` to preserve Unicode characters.
* Generator pattern ensures memory efficiency for large datasets.
* Session is passed as argument (not created inside function) per patterns.md.
