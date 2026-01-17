# Ticket: work-summarization.T09 - Summary Storage: JSON Parsing and Database Persistence

## Source

* Spec: documentation/work/work-summarization.spec.md
* Patterns: documentation/patterns.md

## Goal

* Parse JSON responses from LLM containing per-heading summaries
* Validate response format and heading IDs
* Store summaries in `summary_results` table with proper error handling

## Phase

* Core Modules

## Scope

### In scope

* New module `src/vulcanlab/summarization/summary_storage.py`
* JSON parsing and validation
* Database persistence to `summary_results` table
* Error handling for malformed responses
* Support for regeneration (delete existing before insert)

### Out of scope

* Prompt generation (T07, T08)
* API endpoints (T10+)
* UI for submitting responses (T13)

## Dependencies

* Depends on: T02 (SummaryResult model), T08 (PromptBatch provides expected heading_ids)
* Unblocks: T11 (API uses this for submit-response endpoint)

## Implementation plan

1. Create `src/vulcanlab/summarization/summary_storage.py`
2. Implement `SummaryParseResult` dataclass:
   - success: bool
   - summaries_saved: int
   - errors: list[str]
   - parsed_items: list[dict] (for debugging)
3. Implement `parse_llm_response(response_json: str) -> tuple[list[dict], list[str]]`:
   - Parse JSON string
   - Validate it's a list
   - Validate each item has "id" (int) and "summary" (str)
   - Return (valid_items, errors)
4. Implement `validate_heading_ids(parsed_items: list[dict], expected_ids: list[int]) -> tuple[list[dict], list[str]]`:
   - Check each parsed id is in expected_ids
   - Warn about unexpected IDs
   - Warn about missing expected IDs
   - Return (valid_items, warnings)
5. Implement `save_summaries(work_id: int, items: list[dict], prompt_index: int, session: Session) -> int`:
   - For each item:
     - Upsert into summary_results (update if exists, insert if not)
     - Set summary_content, prompt_index, updated_at
   - Commit transaction
   - Return count saved
6. Implement `delete_existing_summaries(work_id: int, session: Session) -> int`:
   - Delete all summary_results for work_id
   - Delete all summary_chunks for work_id
   - Return count deleted
   - Used for "regenerate all" option
7. Implement main entry `process_llm_response(work_id: int, prompt_index: int, response_json: str, expected_heading_ids: list[int], session: Session) -> SummaryParseResult`:
   - Parse response
   - Validate heading IDs
   - Save valid summaries
   - Return result with counts and errors
8. Handle edge cases:
   - Invalid JSON syntax
   - JSON is not an array
   - Missing required fields
   - Duplicate IDs in response
   - Empty response

* Patterns to apply:
  * **Session Passed Explicitly** - All DB operations receive session
  * **Error Handling** - Graceful handling, no corruption of existing data
* Deviations (if any):
  * None

## Unit tests (required)

* Add tests for:
  * `parse_llm_response` with valid JSON array
  * `parse_llm_response` with invalid JSON syntax
  * `parse_llm_response` with JSON object (not array)
  * `parse_llm_response` with missing "id" field
  * `parse_llm_response` with missing "summary" field
  * `parse_llm_response` with non-integer id
  * `validate_heading_ids` accepts valid IDs
  * `validate_heading_ids` warns on unexpected IDs
  * `validate_heading_ids` warns on missing expected IDs
  * `save_summaries` inserts new rows
  * `save_summaries` updates existing rows (upsert)
  * `delete_existing_summaries` removes all for work
  * `process_llm_response` end-to-end happy path
  * `process_llm_response` partial success (some valid, some invalid)
* Suggested locations:
  * `tests/unit/test_summary_storage.py`
* Mocking/fakes needed:
  * Mock SQLAlchemy session for DB operations
  * Mock SummaryResult model

## Acceptance criteria (checklist)

* [ ] Valid JSON responses parsed correctly
* [ ] Invalid JSON returns meaningful error message
* [ ] Missing/invalid fields reported per item
* [ ] Unexpected heading IDs flagged as warnings
* [ ] Missing expected IDs flagged as warnings
* [ ] Valid summaries saved to database
* [ ] Upsert behavior works (update existing, insert new)
* [ ] Partial failures don't corrupt existing data
* [ ] Delete function removes all summaries for work
* [ ] Unit tests pass for all scenarios

## Manual verification

* Steps:
  * Create test JSON responses (valid and invalid)
  * Call `process_llm_response` with test data
  * Query `summary_results` table to verify inserts
  * Call again with updated content, verify updates
  * Call `delete_existing_summaries`, verify rows removed
* Expected results:
  * Valid responses create/update rows
  * Invalid responses return errors without DB changes
  * Delete removes all related rows

## Notes

* Requirements covered: R9 (parse JSON, store per heading-chunk), R10 (regenerate option)
* Expected JSON format from LLM:
  ```json
  [
    { "id": 123, "summary": "Section summary in markdown..." },
    { "id": 456, "summary": "Another section summary..." }
  ]
  ```
* Use SQLAlchemy's `merge()` or explicit upsert for update-or-insert behavior
* Transaction should rollback if any save fails
