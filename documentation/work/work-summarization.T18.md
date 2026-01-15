# Ticket: work-summarization.T18 - Logging and Observability

## Source

* Spec: documentation/work/work-summarization.spec.md
* Patterns: documentation/patterns.md

## Goal

* Add comprehensive logging for summarization operations
* Track LLM token usage per summarization
* Enable debugging and cost monitoring

## Phase

* Rollout/Hardening

## Scope

### In scope

* Structured logging throughout summarization modules
* Log: work_id, node counts, timing, errors
* LLM token usage tracking (input/output tokens per call)
* Token usage aggregation per work summarization
* Log levels: INFO for progress, WARNING for recoverable issues, ERROR for failures

### Out of scope

* Metrics/alerting infrastructure (future enhancement)
* Dashboard or UI for viewing logs
* Cost calculation (just raw token counts)

## Dependencies

* Depends on: T07 (LLM module), T08 (orchestrator)
* Unblocks: none (hardening task)

## Implementation plan

1. Review existing logging patterns in project
2. Add logging to orchestrator.py:
   - INFO: "Starting summarization for work {work_id}"
   - INFO: "Selected {n} nodes for summarization"
   - INFO: "Completed node {i}/{total}: {chunk_id}"
   - WARNING: "Escalation triggered for node {chunk_id}"
   - ERROR: "Summarization failed for node {chunk_id}: {error}"
   - INFO: "Summarization completed for work {work_id} in {duration}s"
3. Add logging to llm_summarize.py:
   - DEBUG: "Building prompt for node {chunk_id}, evidence snippets: {n}"
   - INFO: "LLM call completed, tokens: input={input}, output={output}"
   - WARNING: "LLM returned insufficient_evidence for node {chunk_id}"
   - ERROR: "LLM API error: {error}, retry {attempt}/{max}"
4. Add logging to compile.py:
   - INFO: "Generating {output_type} for work {work_id}"
   - INFO: "Derived output {output_type} completed"
5. Implement token tracking:
   - Create dataclass: TokenUsage(input_tokens: int, output_tokens: int, model: str)
   - Track per-call usage in llm_summarize
   - Aggregate in orchestrator per work
   - Log total at end of summarization
6. Add timing instrumentation:
   - Time each major phase (node selection, evidence extraction, LLM call, compile)
   - Log breakdown at end
7. Ensure log format is consistent:
   - Include work_id in all summarization logs
   - Use structured logging where possible
* Patterns to apply:
  * Use Python logging module
  * Consistent log format with existing project
  * Structured key-value pairs for searchability
* Deviations (if any):
  * None

## Unit tests (required)

* Add tests for:
  * Logging calls made at correct points in orchestrator
  * Token usage tracked correctly per LLM call
  * Token usage aggregated correctly per work
  * Error logging includes relevant context
  * Warning logged on escalation trigger
  * Timing information captured
* Suggested locations:
  * tests/unit/summarize/test_logging.py
* Mocking/fakes needed:
  * Mock logger to capture log calls
  * Mock LLM responses with token usage

## Acceptance criteria (checklist)

* [ ] Summarization progress logged with work_id
* [ ] Node completion logged with timing
* [ ] LLM token usage logged per call
* [ ] Total token usage logged per work summarization
* [ ] Errors logged with sufficient context
* [ ] Warnings logged for escalations and retries
* [ ] Log format consistent with project standards
* [ ] All unit tests pass

## Manual verification

* Steps:
  1. Run summarization on a work with logging enabled
  2. Review logs for progress messages
  3. Verify token usage appears in logs
  4. Trigger an error (e.g., invalid work_id) and verify error logging
  5. Review log output for completeness
* Expected results:
  * Full summarization flow visible in logs
  * Token counts accurate
  * Errors clearly logged

## Notes

* Requirements covered: Non-functional observability requirements
* Token usage tracking critical for cost monitoring (LLM costs concern in spec)
* Consider adding optional file-based token usage report
* Log level configuration should use existing project patterns
* Structured logging enables future log aggregation/search
