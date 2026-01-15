# Ticket: work-summarization.T19 - Error Handling and Retry Logic

## Source

* Spec: documentation/work/work-summarization.spec.md
* Patterns: documentation/patterns.md

## Goal

* Implement robust error handling for LLM API failures
* Add exponential backoff retry logic
* Ensure partial recovery works correctly

## Phase

* Rollout/Hardening

## Scope

### In scope

* LLM API retry with exponential backoff (max 3 retries)
* Graceful handling of rate limits, timeouts, network errors
* Node-level error isolation (one node failure doesn't stop all)
* Error state persistence for diagnostics
* Clear error messages for common failure modes

### Out of scope

* Alerting/notification on errors (future)
* Automatic retry of failed works
* Circuit breaker pattern

## Dependencies

* Depends on: T07 (LLM module), T08 (orchestrator)
* Unblocks: none (hardening task)

## Implementation plan

1. Define custom exceptions in src/vulcanlab/summarize/exceptions.py:
   - LLMAPIError(message, status_code, retry_after)
   - LLMRateLimitError(LLMAPIError)
   - LLMTimeoutError(LLMAPIError)
   - SummarizationError(message, work_id, chunk_id)
   - InsufficientEvidenceError(SummarizationError)
2. Implement retry decorator/wrapper in llm_summarize.py:
   - Max retries: 3
   - Exponential backoff: 1s, 2s, 4s (with jitter)
   - Retry on: 429 (rate limit), 500/502/503 (server errors), timeout
   - Don't retry on: 400 (bad request), 401/403 (auth)
3. Handle rate limit specifically:
   - Parse Retry-After header if present
   - Wait specified time before retry
4. Update orchestrator error handling:
   - Catch exceptions per node
   - Log error with context
   - Continue to next node on recoverable errors
   - Mark summarization as failed only on unrecoverable errors
   - Store error details for debugging
5. Implement partial recovery:
   - Track successfully completed nodes
   - On resume, skip already-completed nodes
   - Allow manual retry of failed nodes
6. Add error response helpers:
   - Format error messages for API responses
   - Include actionable guidance (e.g., "Try again later" for rate limits)
7. Handle malformed LLM responses:
   - JSON parse errors
   - Missing required fields
   - Treat as retry-able error (LLM may return valid response on retry)
* Patterns to apply:
  * Global exception handling at API layer
  * Specific exceptions from core module
  * Logging with error context
* Deviations (if any):
  * None

## Unit tests (required)

* Add tests for:
  * Retry logic triggers on 429 error
  * Retry logic triggers on 500 error
  * Retry respects max retry limit
  * Exponential backoff timing correct
  * No retry on 400 error
  * No retry on 401/403 error
  * Retry-After header respected
  * Node error doesn't stop other nodes
  * Failed node recorded for debugging
  * Partial recovery skips completed nodes
  * Malformed JSON response triggers retry
* Suggested locations:
  * tests/unit/summarize/test_error_handling.py
  * tests/unit/summarize/test_retry.py
* Mocking/fakes needed:
  * Mock LLM API with various error responses
  * Mock time.sleep to speed up tests

## Acceptance criteria (checklist)

* [ ] LLM errors trigger retry with exponential backoff
* [ ] Max 3 retries enforced
* [ ] Rate limits handled with Retry-After respect
* [ ] Non-retryable errors fail immediately
* [ ] Node failures isolated (don't stop summarization)
* [ ] Failed nodes recorded with error details
* [ ] Partial recovery works correctly
* [ ] Clear error messages for users
* [ ] All unit tests pass

## Manual verification

* Steps:
  1. Simulate LLM rate limit (mock or force)
  2. Verify retry occurs with backoff
  3. After max retries, verify failure logged
  4. Run summarization on work with one problematic section
  5. Verify other nodes complete successfully
  6. Check error details for failed node
* Expected results:
  * Retry logic functions correctly
  * Partial failures handled gracefully
  * Error context available for debugging

## Notes

* Requirements covered: Non-functional reliability requirements
* Exponential backoff formula: delay = base * (2 ^ attempt) + random_jitter
* Jitter helps avoid thundering herd on rate limit recovery
* Consider adding circuit breaker for repeated failures (future enhancement)
* Error details should not include sensitive data (API keys, etc.)
