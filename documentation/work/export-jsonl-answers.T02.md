# Ticket: export-jsonl-answers.T02 - API Endpoint for JSONL Export

## Source

* Spec: documentation/work/export-jsonl-answers.spec.md
* Patterns: documentation/patterns.md

## Goal

* Expose the JSONL export functionality via a RESTful API endpoint.
* Return a streaming response with correct Content-Type and Content-Disposition headers.
* Include unit tests for the endpoint logic.

## Scope

### In scope

* API endpoint `GET /api/v1/eval/experiments/{experiment_id}/export-jsonl` in `src/vulcanlab_api/routers/eval.py`.
* Use `StreamingResponse` to stream the generator from the core module.
* Set Content-Type to `application/x-ndjson`.
* Set Content-Disposition header for file download with correct filename.
* Add logging for the export event.
* Unit tests for endpoint response headers and status codes.

### Out of scope

* Core JSONL generation logic (T01).
* Frontend UI changes (T03).
* Integration tests with real database.

## Dependencies

* Depends on: T01 (core export function)
* Unblocks: T03

## Implementation plan

* Open `src/vulcanlab_api/routers/eval.py`.
* Add new endpoint function similar to the existing CSV export endpoint pattern.
* Define route: `@router.get("/experiments/{experiment_id}/export-jsonl")`.
* Get database session using `get_session()`.
* Call `export_experiment_answers_to_jsonl(session, experiment_id)` from core module.
* Wrap the generator in `StreamingResponse(generator, media_type="application/x-ndjson")`.
* Set `Content-Disposition: attachment; filename="experiment_{experiment_id}_answers.jsonl"` header.
* Add error handling: if experiment doesn't exist, raise `HTTPException(404)`.
* Add logging to track experiment ID and export initiation.
* Patterns to apply:
    * API Layer Routing - Thin router calling core module, no business logic in API layer.
    * Error Handling - Raise `HTTPException` for client errors, let global handler catch 500s.
    * Configuration - Use standard session management from `vulcanlab.data.database`.
* Deviations (if any):
    * None.

## Unit tests (required)

* Add tests for:
    * Successful export: Mock core function, verify response status 200, Content-Type, Content-Disposition headers.
    * Experiment not found: Mock core function to raise exception or return empty, verify 404 response.
    * Streaming behavior: Verify response is a `StreamingResponse` instance.
    * Filename format: Verify Content-Disposition header contains correct filename pattern.
* Suggested locations:
    * `tests/unit/test_api_jsonl_export.py` (new file) or add to existing API test file.
* Mocking/fakes needed:
    * Mock `export_experiment_answers_to_jsonl` function from core module.
    * Mock database session and `get_session()`.

## Acceptance criteria (checklist)

* [ ] Endpoint `GET /api/v1/eval/experiments/{experiment_id}/export-jsonl` exists in `src/vulcanlab_api/routers/eval.py`.
* [ ] Endpoint returns `StreamingResponse` with `media_type="application/x-ndjson"`.
* [ ] Content-Disposition header is set to `attachment; filename="experiment_{id}_answers.jsonl"`.
* [ ] Endpoint returns 200 on success, 404 if experiment not found.
* [ ] Endpoint calls the core module function `export_experiment_answers_to_jsonl`.
* [ ] Unit tests verify response headers, status codes, and streaming behavior.
* [ ] All unit tests pass with mocked dependencies.

## Manual verification

* Steps:
    * Run unit tests: `pytest tests/unit/test_api_jsonl_export.py -v`.
    * Start the API server locally.
    * Use `curl` or browser to hit the endpoint: `GET http://localhost:8000/api/v1/eval/experiments/1/export-jsonl`.
    * Verify response headers include correct Content-Type and Content-Disposition.
    * Save the response to a file and verify it's valid JSONL.
* Expected results:
    * Unit tests pass.
    * Endpoint returns JSONL content with correct headers.
    * File downloads with correct filename in browser.

## Notes

* Requirements covered: R4, R5, R6.
* Follow the same pattern as the existing CSV export endpoint for consistency.
* Use `StreamingResponse` to avoid loading entire dataset into memory.
* Ensure the route is registered with `/api/v1` prefix in `main.py` (should already be configured for eval router).
* Log the export event at INFO level with experiment ID.
