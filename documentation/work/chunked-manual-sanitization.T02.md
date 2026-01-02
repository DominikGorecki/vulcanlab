# Ticket: chunked-manual-sanitization.T02 - Core Batching Logic and Utilities

## Source

* Spec: documentation/work/chunked-manual-sanitization.spec.md
* Patterns: documentation/patterns.md

## Goal

* Implement core batching functions for splitting condensed documents, extracting hierarchical context, generating batched prompts, and merging batch results.
* Provide framework-independent business logic for batched sanitization workflow.
* Ensure all functions are unit tested with mocked database sessions.

## Scope

### In scope

* Core module functions in `src/vulcanlab/simple_conversion/`:
  * `split_condensed_into_batches(condensed_doc, batch_size)` - Split condensed document into batches of N headings.
  * `extract_hierarchical_context(previous_batch_results, current_heading_level, max_headings)` - Extract higher-level headings from previous batches for context.
  * `generate_batched_prompt(batch_data, context_headings, batch_index, total_batches, template)` - Generate prompt for one batch with context.
  * `merge_batch_results(batch_results)` - Combine all batch results into final sanitized modifications JSON.
  * `validate_batch_response(llm_response_json)` - Validate batch LLM response schema and line numbers.
* Database access functions for batch progress:
  * `create_batch_progress(work_id, total_batches, session)` - Initialize batch progress record.
  * `get_batch_progress(work_id, session)` - Retrieve batch progress state.
  * `update_batch_progress(work_id, batch_index, batch_result, batch_size, session)` - Update progress after batch submission.
* Comprehensive unit tests for all functions.

### Out of scope

* API endpoints (T03).
* UI components (T05, T06).
* Settings page changes (T04).
* Template creation (T01 - already done).

## Dependencies

* Depends on: T01 (database table must exist for DB functions)
* Unblocks: T03, T05

## Implementation plan

* Create new file `src/vulcanlab/simple_conversion/batch_sanitization.py`.
* Implement `split_condensed_into_batches(condensed_doc: str, batch_size: int) -> List[Dict]`:
  * Parse condensed document to extract heading entries (line number, level, text, context).
  * Split into batches of `batch_size` headings.
  * Preserve line numbers from original condensed document.
  * Return list of batch dicts with `batch_index`, `headings`, `start_line`, `end_line`.
* Implement `extract_hierarchical_context(previous_batch_results: List[Dict], current_heading_level: int, max_headings: int) -> List[Dict]`:
  * Walk backwards through previous batch results.
  * Extract headings at level `current_heading_level - 1` (next higher level).
  * Limit to `max_headings` (default 25).
  * Return list of context heading dicts with `line`, `level`, `text`.
* Implement `generate_batched_prompt(batch_data: Dict, context_headings: List[Dict], batch_index: int, total_batches: int, template: str) -> str`:
  * Load template content (from T01 template).
  * Substitute variables: `{condensed_document}` with batch headings, `{context_headings}` with context, `{batch_range}` with heading range.
  * Return formatted prompt string.
* Implement `merge_batch_results(batch_results: List[Dict]) -> Dict`:
  * Concatenate all batch `modifications` arrays in order.
  * Deduplicate by line number if needed (last modification wins).
  * Return single merged modifications JSON.
* Implement `validate_batch_response(llm_response_json: Dict) -> bool`:
  * Check JSON schema: `{"modifications": [{"line": int, "action": str, "vectorize": bool, "new": str (optional)}]}`.
  * Validate actions are "keep", "change", or "remove".
  * Validate "new" is present only when action is "change".
  * Raise ValueError with descriptive message if invalid.
* Implement database functions in same file:
  * `create_batch_progress(work_id, total_batches, session)` - Insert new record.
  * `get_batch_progress(work_id, session)` - Query by work_id.
  * `update_batch_progress(work_id, batch_index, batch_result, batch_size, session)` - Update batch_results, batch_sizes, current_batch_index.
* Patterns to apply:
  * **Core Module Independence** - No FastAPI imports, pure Python logic.
  * **Database Session Management** - Session passed explicitly as argument.
  * **Error Handling** - Raise specific exceptions (ValueError for validation, KeyError for missing data).
* Deviations (if any):
  * None; follows established patterns.

## Unit tests (required)

* Add tests for:
  * `split_condensed_into_batches`:
    * Test with 5000 headings, batch size 5000 (1 batch).
    * Test with 12000 headings, batch size 5000 (3 batches).
    * Test with 5001 headings, batch size 5000 (2 batches).
    * Verify batch indexes, start_line, end_line are correct.
    * Verify line numbers preserved from condensed doc.
  * `extract_hierarchical_context`:
    * Test with H3 headings in current batch, extract H2 from previous batches.
    * Test limit to 25 headings.
    * Test with no previous batches (empty context).
    * Test with mixed heading levels.
  * `generate_batched_prompt`:
    * Test variable substitution (condensed_document, context_headings, batch_range).
    * Test with empty context headings.
    * Test batch_index and total_batches formatting.
  * `merge_batch_results`:
    * Test merging 3 batches with non-overlapping line numbers.
    * Test deduplication with overlapping line numbers (last wins).
    * Test ordering (modifications sorted by line number).
  * `validate_batch_response`:
    * Test valid JSON with all fields.
    * Test invalid action (not keep/change/remove).
    * Test missing "new" when action is "change".
    * Test extra "new" when action is "keep" or "remove".
    * Test missing "modifications" key.
  * Database functions:
    * Test `create_batch_progress` inserts record.
    * Test `get_batch_progress` retrieves record.
    * Test `update_batch_progress` updates fields correctly.
* Suggested locations:
  * `tests/unit/test_batch_sanitization.py`
* Mocking/fakes needed:
  * Mock SQLAlchemy session for database functions.
  * Mock template file reading (use string template in tests).

## Acceptance criteria (checklist)

* [ ] File `src/vulcanlab/simple_conversion/batch_sanitization.py` created.
* [ ] Function `split_condensed_into_batches` implemented and tested.
* [ ] Function `extract_hierarchical_context` implemented and tested.
* [ ] Function `generate_batched_prompt` implemented and tested.
* [ ] Function `merge_batch_results` implemented and tested.
* [ ] Function `validate_batch_response` implemented and tested.
* [ ] Database functions `create_batch_progress`, `get_batch_progress`, `update_batch_progress` implemented and tested.
* [ ] All unit tests pass.
* [ ] Performance requirement met: batch splitting <500ms for 50,000 headings.

## Manual verification

* Steps:
  * Create test condensed document with 12,000 heading entries.
  * Call `split_condensed_into_batches(test_doc, 5000)`.
  * Verify returns 3 batches with correct line ranges.
  * Create mock previous batch results.
  * Call `extract_hierarchical_context(previous_results, 3, 25)`.
  * Verify returns up to 25 H2 headings from previous batches.
  * Call `generate_batched_prompt(batch_data, context, 0, 3, template)`.
  * Verify prompt contains batch range "1-5000 of 12000".
  * Create 3 mock batch results.
  * Call `merge_batch_results(batch_results)`.
  * Verify returns single merged modifications JSON with all line numbers.
  * Call `validate_batch_response(valid_json)` and `validate_batch_response(invalid_json)`.
  * Verify valid passes, invalid raises ValueError.
* Expected results:
  * All functions return expected outputs.
  * Batch splitting preserves line numbers.
  * Context extraction limits to 25 headings.
  * Prompt generation includes all variables.
  * Merge preserves ordering and deduplicates.
  * Validation correctly identifies invalid schemas.

## Notes

* Requirements covered: R2 (batch size handling), R3 (context extraction), R4 (partial - DB functions), R6 (validation), R12 (vectorize flag in schema), R13 (merge produces final result).
* Batch splitting logic should handle edge cases: last batch smaller than batch_size, exact multiples, single heading batches.
* Context extraction should handle case where no higher-level headings exist in previous batches.
* Merge logic should preserve vectorize flags from all batches.
* Performance critical: Avoid re-parsing condensed document multiple times; parse once and cache.
