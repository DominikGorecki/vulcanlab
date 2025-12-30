# Ticket: export-csv-evaluations.T02 - Core Logic: CSV Formatting and Sanitization

## Source

* Spec: documentation/work/export-csv-evaluations.spec.md
* Patterns: documentation/patterns.md

## Goal

* Implement the CSV formatting logic using the standard Python `csv` module.
* Ensure all text fields (prompts, justifications) are properly sanitized and escaped.
* Dynamically generate columns for all evaluation dimensions present in the experiment.

## Scope

### In scope

* Backend: Complete implementation of `export_experiment_evaluations_to_csv` in `src/vulcanlab/eval/evaluations.py`.
* Logic: Dynamic discovery of all unique dimension names for the CSV header.
* Formatting: Using `csv.DictWriter` and `io.StringIO` to generate the CSV string.
* Sanitization: Ensuring correct escaping of commas, quotes, and newlines in text fields.

### Out of scope

* API endpoint implementation (handled in T03).
* UI integration (handled in T04).

## Dependencies

* Depends on: export-csv-evaluations.T01
* Unblocks: export-csv-evaluations.T02

## Implementation plan

* Finalize `export_experiment_evaluations_to_csv` in `src/vulcanlab/eval/evaluations.py`.
* Implement logic to collect all unique `dimension_name` values from `ExperimentDimensionResult` across the experiment's evaluations.
* Order headers: `prompt`, `grouping_id`, `overall_score`, followed by alphabetical dimension names, then `justification`.
* Use `csv.DictWriter` with `csv.QUOTE_MINIMAL` to write the CSV to an `io.StringIO` buffer.
* Ensure the function returns the full CSV string.
* Patterns to apply:
    * Core Module Logic - Encapsulating formatting logic in the core module.

## Unit tests (required)

* Add tests for:
    * CSV header generation including custom dimensions.
    * Proper escaping of special characters (commas, newlines, double quotes) in prompt text.
    * Correct mapping of dimension scores to their respective columns.
    * Handling missing dimension scores for specific rows (blank values).
* Suggested locations:
    * `tests/unit/test_eval_export_csv.py`
* Mocking/fakes needed:
    * Mock evaluation data retrieved from T01.

## Acceptance criteria (checklist)

* [ ] CSV header follows the required order (R1).
* [ ] All dimension names are included as columns.
* [ ] Prompt and justification text is correctly escaped (R4).
* [ ] The output is a valid CSV string ready for download.

## Manual verification

* Steps:
    * This ticket is internal logic; manual verification will be performed after T03 is implemented.
    * Verify via unit tests.
* Expected results:
    * Unit tests pass with correctly formatted and sanitized CSV output.

## Notes

* Requirements covered: R1, R4
* The `csv` module handles most sanitization automatically when using `DictWriter`.

