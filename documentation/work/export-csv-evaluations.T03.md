# Ticket: export-csv-evaluations.T03 - API Layer: CSV Export Endpoint and Streaming

## Source

* Spec: documentation/work/export-csv-evaluations.spec.md
* Patterns: documentation/patterns.md

## Goal

* Expose the CSV export functionality via a FastAPI endpoint.
* Implement file streaming and proper response headers for browser downloads.
* Ensure the downloaded filename matches the required pattern.

## Scope

### In scope

* API: New route `GET /api/v1/eval/experiments/{id}/export-csv` in `src/vulcanlab_api/routers/eval.py`.
* API: Use `StreamingResponse` or `Response` to return the CSV content.
* Configuration: Setting the `Content-Disposition` header with the correct filename.
* Error Handling: Returning 404 if the experiment does not exist.

### Out of scope

* Frontend implementation (handled in T04).

## Dependencies

* Depends on: export-csv-evaluations.T02
* Unblocks: export-csv-evaluations.T04

## Implementation plan

* Add a new endpoint to the `eval` router in `src/vulcanlab_api/routers/eval.py`.
* Import `export_experiment_evaluations_to_csv` from the core module.
* Call the core function within a `get_session()` context.
* Construct the response with `media_type="text/csv"`.
* Set the `Content-Disposition` header to `attachment; filename=experiment_[id]_evaluations.csv`.
* Handle `ValueError` exceptions and return appropriate `HTTPException` (e.g., 404 for missing experiment).
* Patterns to apply:
    * API Layer Routing - Thin router calling core logic.
    * Error Handling - Standard FastAPI exception handling.

## Unit tests (required)

* Add tests for:
    * Successful CSV download response and status code.
    * Correct `Content-Disposition` header and filename.
    * 404 error when experiment ID is invalid.
    * 400 or 404 error when experiment has no evaluations.
* Suggested locations:
    * `tests/unit/test_eval_api_export.py`
* Mocking/fakes needed:
    * Mock `export_experiment_evaluations_to_csv` core function.

## Acceptance criteria (checklist)

* [ ] API endpoint `/api/v1/eval/experiments/{id}/export-csv` is functional (R5).
* [ ] Response has correct `text/csv` media type.
* [ ] Downloaded filename follows the pattern `experiment_[id]_evaluations.csv` (R6).
* [ ] Endpoint handles errors gracefully.

## Manual verification

* Steps:
    * Start the API server.
    * Identify an experiment ID with evaluations.
    * Navigate to `http://localhost:8000/api/v1/eval/experiments/[id]/export-csv` in a browser or use `curl -O`.
* Expected results:
    * A CSV file is downloaded with the correct name and content.

## Notes

* Requirements covered: R5, R6
* Ensure `StreamingResponse` is used if the CSV data is large, or a simple `Response` if returning the string buffer directly.

