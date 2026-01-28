# Ticket: expand-answer.T06 - Hardening: Error Handling, Logging, and Observability

## Source

* Spec: documentation/work/expand-answer.spec.md
* Patterns: documentation/patterns.md

## Goal

* Add comprehensive error handling for partial failures
* Implement structured logging with expansion_id and section_id context
* Ensure section-level isolation so failures do not cascade
* Add database transaction scoping per-section

## Scope

### In scope

* Error handling in core expansion functions
* Section-level transaction isolation (failures do not rollback other sections)
* Structured logging with expansion_id/section_id in log context
* LLM response validation and graceful degradation
* API error responses with meaningful messages
* Retry logic for transient failures (LLM timeouts, rate limits)

### Out of scope

* Metrics/telemetry integration (can be added later)
* Alerting configuration
* Performance optimization beyond spec requirements

## Dependencies

* Depends on: T02 (core logic), T03 (API endpoints)
* Unblocks: none (final hardening ticket)

## Implementation plan

1. Add structured logging to core expansion module:
   - Use Python `logging` with `extra` dict for context
   - Log expansion creation, section transitions, failures
   - Include `expansion_id`, `section_id`, `status` in log context
   - Example: `logger.info("Section status changed", extra={"expansion_id": 1, "section_id": 2, "status": "expanding"})`
2. Implement section-level transaction isolation:
   - Each section operation (expand, generate) uses its own transaction
   - On failure, only that section's changes are rolled back
   - Update section status to `failed` with error_message on exception
   - Other sections continue processing in automatic mode
3. Add error handling to breakdown logic:
   - Validate LLM response is valid JSON
   - Validate section count is 3-7
   - Validate each section has required fields (heading, summary, expansion_prompt)
   - On validation failure, set expansion status to `failed` with descriptive error
4. Add error handling to section processing:
   - Catch LLM API errors (timeout, rate limit, invalid response)
   - Catch retrieval errors (embedding service, vector DB)
   - Store error_message in section record
   - Set section status to `failed`
   - Continue with next section in automatic mode
5. Add retry logic for transient failures:
   - Implement exponential backoff for LLM calls
   - Configurable max retries (default: 3)
   - Log retry attempts with context
6. Update API error responses:
   - Return 400 with message for validation errors
   - Return 409 for conflict (expansion already exists)
   - Return 422 for invalid state transitions
   - Include expansion/section status in error response body
7. Add error state display in UI (coordinate with T05):
   - Show error_message in section detail when failed
   - Highlight failed sections visually
   - Show overall error state in expansion header
8. Write unit tests for error scenarios

* Patterns to apply:
  * Error Handling - Use global handlers, raise specific exceptions
  * Observability - Log with context for debugging
  * Reliability - Section-level isolation, graceful degradation

* Deviations (if any):
  * None

## Unit tests (required)

* Add tests for:
  * `test_breakdown_invalid_json_sets_failed` - expansion fails gracefully on bad LLM response
  * `test_breakdown_wrong_section_count_sets_failed` - rejects <3 or >7 sections
  * `test_expand_section_llm_error_isolated` - failure does not affect other sections
  * `test_expand_section_stores_error_message` - error details captured
  * `test_generate_section_timeout_retries` - transient failure triggers retry
  * `test_generate_section_max_retries_fails` - gives up after max retries
  * `test_automatic_mode_continues_after_failure` - other sections still process
  * `test_combine_skips_failed_sections` - or requires all complete (per spec decision)
  * `test_api_returns_400_on_validation_error` - meaningful error response
  * `test_api_returns_409_on_duplicate` - conflict for existing expansion

* Suggested locations:
  * `tests/unit/expansion/test_error_handling.py`
  * `tests/unit/api/routers/test_expansions_errors.py`

* Mocking/fakes needed:
  * Mock LLM client to simulate errors (timeout, rate limit, bad response)
  * Mock retrieval service to simulate failures
  * Mock database session for transaction testing

## Acceptance criteria (checklist)

* [ ] LLM errors in breakdown set expansion status to `failed` with error message
* [ ] LLM errors in section processing set section status to `failed` with error message
* [ ] Failed sections do not prevent other sections from processing
* [ ] Transient failures (timeout, rate limit) trigger retry with exponential backoff
* [ ] Logging includes expansion_id and section_id in all relevant log entries
* [ ] API returns appropriate error codes (400, 409, 422) with meaningful messages
* [ ] Section error_message visible in UI when section failed
* [ ] Database transactions scoped per-section (no large rollbacks)
* [ ] All unit tests pass

## Manual verification

* Steps:
  1. Create expansion with a result that will cause breakdown to fail (mock or use edge case)
  2. Verify expansion status is `failed` with error message
  3. Create expansion and simulate section failure (e.g., disconnect from embedding service temporarily)
  4. Verify failed section shows error, other sections continue
  5. Retry failed section, verify it reprocesses
  6. Check application logs for structured log entries with expansion/section context
  7. Verify API error responses include useful error messages

* Expected results:
  * Failures are isolated and recoverable
  * Error messages are informative for debugging
  * Logs enable tracing of expansion lifecycle

## Notes

* Requirements covered: R7 (status tracking), R8 (retry capability), reliability non-functional requirements
* The spec states "Failed sections should not block other sections from completing"
* Per spec: "Database transactions should be scoped per-section to avoid large rollbacks"
* Consider whether `combine` should fail if any section failed, or skip failed sections - spec implies all must complete (verify with user if unclear)
* Exponential backoff: 1s, 2s, 4s for retries (configurable)
