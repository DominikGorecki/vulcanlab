# Ticket: chunked-manual-sanitization.T03 - API Endpoints for Batched Workflow

## Source

* Spec: documentation/work/chunked-manual-sanitization.spec.md
* Patterns: documentation/patterns.md

## Goal

* Implement API endpoints for batched manual sanitization workflow.
* Provide HTTP contracts for generating batched prompts, submitting batch results, and retrieving batch status.
* Ensure endpoints integrate with core batching logic from T02.

## Scope

### In scope

* Three new API endpoints in `src/vulcanlab_api/routers/simple_conversion.py`:
  * `GET /api/simple-conversion/manual-prompt-batched/{work_id}?batch_size={N}` - Get prompt for next batch.
  * `POST /api/simple-conversion/manual-submit-batched/{work_id}` - Submit LLM response for current batch.
  * `GET /api/simple-conversion/batched-status/{work_id}` - Get current batch progress.
* Request/response models (Pydantic schemas) for all endpoints.
* Integration with core functions from T02.
* Unit tests for endpoint logic (mocked DB and core functions).

### Out of scope

* Frontend UI changes (T05, T06).
* Settings page changes (T04).
* Single-step workflow modifications (must remain unchanged per R8).

## Dependencies

* Depends on: T01 (database table), T02 (core functions)
* Unblocks: T05, T06

## Implementation plan

* Define Pydantic request/response models in `src/vulcanlab_api/routers/simple_conversion.py` or separate schemas file:
  * `BatchedPromptRequest` (query param: batch_size: Optional[int]).
  * `BatchedPromptResponse` (work_id, classification, batch_index, total_batches, batch_size_used, prompt, instructions, heading_range, context_headings_count).
  * `BatchedSubmitRequest` (llm_response: str).
  * `BatchedSubmitResponse` (success, batch_index, total_batches, is_complete, next_batch_index OR sanitized_work_id).
  * `BatchedStatusResponse` (work_id, batched_enabled, current_batch, total_batches, completed_batches, batch_sizes_used, can_resume).
* Implement `GET /api/simple-conversion/manual-prompt-batched/{work_id}`:
  * Load work and parsed_markdown from database.
  * Verify classification is "large" (raise HTTPException 400 if not).
  * Get batch progress from database via `get_batch_progress(work_id, session)`.
  * If no progress record, check heading count against global `batch_size_headings` config.
  * If exceeds threshold, create initial batch progress via `create_batch_progress(work_id, total_batches, session)`.
  * Use query param `batch_size` if provided, else use global config value.
  * Call `split_condensed_into_batches(condensed_doc, batch_size)` from T02.
  * Get current batch data based on `current_batch_index`.
  * Extract context from previous batches via `extract_hierarchical_context(...)`.
  * Generate prompt via `generate_batched_prompt(...)`.
  * Return `BatchedPromptResponse`.
* Implement `POST /api/simple-conversion/manual-submit-batched/{work_id}`:
  * Load batch progress from database.
  * Validate LLM response via `validate_batch_response(llm_response_json)` from T02.
  * If valid, update progress via `update_batch_progress(work_id, batch_index, batch_result, batch_size, session)`.
  * Increment `current_batch_index`.
  * If all batches complete, merge results via `merge_batch_results(batch_results)`.
  * Apply merged results to existing sanitization flow (call existing `apply_sanitization` logic).
  * Return `BatchedSubmitResponse` with `is_complete: true` and `sanitized_work_id`.
  * If not complete, return `is_complete: false` and `next_batch_index`.
* Implement `GET /api/simple-conversion/batched-status/{work_id}`:
  * Load batch progress from database.
  * If no record, return `batched_enabled: false`.
  * If record exists, return current state: current_batch, total_batches, completed_batches, batch_sizes_used, can_resume: true.
* Add logging for batch progression events (batch N of M started, completed, batch size used).
* Patterns to apply:
  * **API Versioning** - Endpoints use `/api/simple-conversion` prefix (existing v1 implied).
  * **Error Handling** - Raise HTTPException for client errors (400 for validation, 404 for not found).
  * **Session Management** - Session dependency injected via `Depends(get_db_session)`.
* Deviations (if any):
  * None; follows established patterns.

## Unit tests (required)

* Add tests for:
  * `GET /api/simple-conversion/manual-prompt-batched/{work_id}`:
    * Test with valid work_id and "large" classification (returns prompt).
    * Test with "small" classification (returns 400 error).
    * Test with custom batch_size query param (uses custom size).
    * Test without batch_size param (uses global config).
    * Test with existing progress record (resumes from current batch).
    * Test with no progress record (creates new record).
  * `POST /api/simple-conversion/manual-submit-batched/{work_id}`:
    * Test with valid LLM response (updates progress, returns next batch).
    * Test with invalid LLM response (returns 400 error, does not update progress).
    * Test final batch submission (merges results, returns is_complete: true).
    * Test intermediate batch submission (returns is_complete: false).
  * `GET /api/simple-conversion/batched-status/{work_id}`:
    * Test with existing progress (returns status).
    * Test with no progress (returns batched_enabled: false).
* Suggested locations:
  * `tests/unit/test_simple_conversion_batched_api.py`
* Mocking/fakes needed:
  * Mock database session and queries.
  * Mock core functions from T02 (`split_condensed_into_batches`, `extract_hierarchical_context`, `generate_batched_prompt`, `merge_batch_results`, `validate_batch_response`).
  * Mock config loader to return test values for `batch_size_headings` and `batch_context_headings`.

## Acceptance criteria (checklist)

* [ ] Endpoint `GET /api/simple-conversion/manual-prompt-batched/{work_id}` implemented.
* [ ] Endpoint `POST /api/simple-conversion/manual-submit-batched/{work_id}` implemented.
* [ ] Endpoint `GET /api/simple-conversion/batched-status/{work_id}` implemented.
* [ ] Pydantic request/response models defined for all endpoints.
* [ ] Endpoints return correct HTTP status codes (200, 400, 404).
* [ ] Logging added for batch progression events (batch N of M started, completed).
* [ ] Invalid batch responses return 400 error without updating progress.
* [ ] Final batch submission triggers merge and applies sanitization.
* [ ] All unit tests pass.

## Manual verification

* Steps:
  * Start API server: `uvicorn vulcanlab_api.main:app --reload`.
  * Create test work with "large" classification and 12,000 headings.
  * Call `GET /api/simple-conversion/manual-prompt-batched/{work_id}` via curl or Postman.
  * Verify response includes batch_index: 0, total_batches: 3, prompt text.
  * Submit valid batch 1 response via `POST /api/simple-conversion/manual-submit-batched/{work_id}`.
  * Verify response includes is_complete: false, next_batch_index: 1.
  * Call `GET /api/simple-conversion/batched-status/{work_id}`.
  * Verify status shows current_batch: 1, completed_batches: [0].
  * Submit batches 2 and 3.
  * Verify final batch response includes is_complete: true, sanitized_work_id.
  * Call status endpoint again, verify batched_enabled: true (or progress cleared).
* Expected results:
  * All endpoints return correct data.
  * Progress updates after each batch submission.
  * Final batch triggers merge and sanitization.
  * Invalid responses return 400 errors.
  * Logs show batch progression events.

## Notes

* Requirements covered: R1 (partial - detection logic), R2 (batch size handling), R4 (progress storage), R5 (resume via status endpoint), R6 (validation), R11 (dynamic batch size via query param), R13 (merge and proceed to sanitization).
* Integration point with existing sanitization flow: After merge, call existing `apply_sanitization(work_id, modifications_json, session)` or equivalent function.
* Ensure existing single-step endpoints (`/api/simple-conversion/manual-prompt/{work_id}`, `/api/simple-conversion/manual-submit/{work_id}`) remain unchanged per R8.
* Dynamic batch sizing: When user provides custom batch_size in query param, recalculate total_batches based on remaining headings.
