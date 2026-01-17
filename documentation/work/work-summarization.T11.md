# Ticket: work-summarization.T11 - API Router: Submit Response and Retrieval Endpoints

## Source

* Spec: documentation/work/work-summarization.spec.md
* Patterns: documentation/patterns.md

## Goal

* Add endpoint to submit LLM responses and store parsed summaries
* Add endpoints to retrieve summaries (single work, list all)
* Add settings endpoints for configuration management

## Phase

* APIs

## Scope

### In scope

* `POST /api/v1/summarize/works/{work_id}/submit-response` endpoint
* `GET /api/v1/summarize/works/{work_id}/summary` endpoint
* `GET /api/v1/summarize/works` endpoint (list works with summaries)
* `GET /api/v1/summarize/settings` endpoint
* `PUT /api/v1/summarize/settings` endpoint
* Pydantic schemas for all endpoints

### Out of scope

* Core module logic (already in T09)
* Frontend integration (T13+)

## Dependencies

* Depends on: T09 (summary_storage module), T10 (router exists)
* Unblocks: T13, T14, T15, T16

## Implementation plan

1. Extend `src/vulcanlab_api/schemas/summarize.py`:
   - `SubmitResponseRequest`: prompt_index, response_json
   - `SubmitResponseResponse`: success, summaries_saved, errors
   - `SummarySection`: chunk_id, heading, summary_content, start_line
   - `WorkSummaryResponse`: work_id, work_title, sections (list[SummarySection])
   - `WorkSummaryListItem`: work_id, title, summary_count, last_updated
   - `WorkSummaryListResponse`: works (list[WorkSummaryListItem])
   - `SummarizeSettingsSchema`: all settings fields
2. Implement `POST /api/v1/summarize/works/{work_id}/submit-response`:
   - Validate work exists
   - Look up expected heading_ids from most recent prompt generation (store in session or derive from summary_chunks)
   - Call `process_llm_response()` with response_json
   - Return success/error counts
3. Implement `GET /api/v1/summarize/works/{work_id}/summary`:
   - Query summary_results for work_id
   - Join with chunks to get heading info (first line, start_line)
   - Order by start_line ascending
   - Return WorkSummaryResponse
4. Implement `GET /api/v1/summarize/works`:
   - Query summary_results grouped by work_id
   - Join with works for title
   - Count summaries per work
   - Get max updated_at as last_updated
   - Return WorkSummaryListResponse
5. Implement `GET /api/v1/summarize/settings`:
   - Query summarize_settings (single row)
   - Return as SummarizeSettingsSchema
6. Implement `PUT /api/v1/summarize/settings`:
   - Accept SummarizeSettingsSchema
   - Update summarize_settings row
   - Return updated settings
7. Add error handling:
   - 404 if work not found
   - 400 if no prompt has been generated (for submit)
   - 404 if work has no summaries (for summary retrieval)

* Patterns to apply:
  * **API Versioning** - All routes under `/api/v1`
  * **Thin API Layer** - Orchestrate core modules
  * **Error Handling** - HTTPException for client errors
* Deviations (if any):
  * None

## Unit tests (required)

* Add tests for:
  * Submit-response parses valid JSON and saves
  * Submit-response returns errors for invalid JSON
  * Submit-response returns partial success for mixed valid/invalid
  * Get summary returns sections in start_line order
  * Get summary returns 404 for work without summaries
  * List works returns only works with summaries
  * List works includes correct counts and dates
  * Get settings returns current values
  * Put settings updates values
  * Put settings validates input (e.g., positive integers)
* Suggested locations:
  * `tests/unit/test_summarize_router_submit.py`
  * `tests/unit/test_summarize_router_retrieval.py`
  * `tests/unit/test_summarize_router_settings.py`
* Mocking/fakes needed:
  * Mock database session
  * Mock summary_storage.process_llm_response
  * Mock summary_results and summarize_settings queries

## Acceptance criteria (checklist)

* [ ] Submit endpoint parses JSON and stores summaries
* [ ] Submit endpoint returns meaningful errors
* [ ] Get summary endpoint returns ordered sections
* [ ] List endpoint returns works with summary counts
* [ ] Settings GET returns current configuration
* [ ] Settings PUT updates configuration
* [ ] All endpoints return proper error codes
* [ ] Unit tests pass for all endpoints

## Manual verification

* Steps:
  * Generate prompts for a work (T10)
  * Copy prompt, run through LLM, get JSON response
  * POST response to submit-response endpoint
  * GET /api/v1/summarize/works/{work_id}/summary
  * Verify summary sections appear in document order
  * GET /api/v1/summarize/works to see work in list
  * PUT /api/v1/summarize/settings with new values, verify they persist
* Expected results:
  * Summaries stored and retrievable
  * List shows summarized works
  * Settings changes are saved

## Notes

* Requirements covered: R9, R10, R11, R12 (via API), Settings management
* For submit-response, need to track which prompt_index corresponds to which heading_ids
  * Option A: Store in summary_chunks with a batch marker
  * Option B: Re-derive from rankings (less reliable)
  * Recommend Option A: add prompt_index to summary_chunks during generate-prompts
* List endpoint enables Summaries page in UI (T14)
