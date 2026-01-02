# Ticket: chunked-manual-sanitization.T06 - Dynamic Batch Sizing and Resume Functionality

## Source

* Spec: documentation/work/chunked-manual-sanitization.spec.md
* Patterns: documentation/patterns.md

## Goal

* Add dynamic batch size adjustment UI to manual page (user can change batch size per-call).
* Implement resume functionality to restore batch progress after browser close/refresh.
* Enable "Regenerate Prompt" button for batch size changes.
* Provide complete batched workflow experience with full flexibility.

## Scope

### In scope

* Input field for batch size adjustment on manual workflow page.
* "Regenerate Prompt" button to fetch new prompt with updated batch size.
* Resume detection and UI on page load (check for in-progress batched workflow).
* Resume message: "Resume from Batch N of M".
* Recalculation of total_batches when batch size changes.
* Unit tests for dynamic sizing and resume logic.

### Out of scope

* Basic batched workflow (T05 - already done).
* Settings page (T04 - already done).
* API endpoints (T03 - already support dynamic sizing via query param).

## Dependencies

* Depends on: T05 (basic batched workflow must exist)
* Unblocks: None (final ticket)

## Implementation plan

* Open `vulcanlab_ui/src/app/simple-conversion/manual/[work_id]/page.tsx`.
* Add state for batch size:
  * `currentBatchSize: number` (initialized from global config or current batch prompt).
* Add input field for batch size adjustment:
  * Label: "Batch Size (Headings)".
  * Input type: number, min: 1000, step: 1000.
  * Default value: current batch size from prompt response or global config.
  * Disabled when batch is submitting.
* Add "Regenerate Prompt" button:
  * Label: "Regenerate Prompt".
  * Disabled when batch size hasn't changed or batch is submitting.
  * On click, call `GET /api/simple-conversion/manual-prompt-batched/{work_id}?batch_size={currentBatchSize}`.
  * Update `currentBatchPrompt` with new prompt.
  * Update UI to show new total_batches and heading_range.
* Implement resume detection on page load:
  * After fetching batch status via `GET /api/simple-conversion/batched-status/{work_id}`:
    * If `batched_enabled: true` and `current_batch > 0`, show resume message.
    * Resume message: "You have an in-progress batched workflow. Resume from Batch {current_batch + 1} of {total_batches}?"
    * Provide "Resume" button to load current batch prompt.
    * Optionally provide "Start Over" button to reset progress (delete batch progress record via API or restart from batch 0).
  * If `batched_enabled: true` and `current_batch === 0`, start from batch 1 (no resume message needed).
* Implement batch size change recalculation:
  * When user changes batch size and clicks "Regenerate Prompt":
    * Send new batch_size to API.
    * API recalculates total_batches based on remaining headings: `total_batches = ceil((total_headings - processed_headings) / new_batch_size) + current_batch`.
    * Update UI to show new total_batches.
* Add validation for batch size input:
  * Minimum 1000 headings.
  * Show inline validation error if < 1000.
* Patterns to apply:
  * **Frontend Page Lifecycle** - Use `usePageData` and `useCallback` for fetching.
  * **Forms** - Use `react-hook-form` or controlled input for batch size field.
  * **Component Composition** - Reuse existing `Input`, `Button`, `Alert` components.
* Deviations (if any):
  * None; follows established patterns.

## Unit tests (required)

* Add tests for:
  * Dynamic batch size adjustment:
    * Test changing batch size from 5000 to 10000.
    * Test clicking "Regenerate Prompt" fetches new prompt with updated batch_size query param.
    * Test total_batches updates after regeneration (e.g., 3 batches -> 2 batches).
  * Resume detection:
    * Test with in-progress workflow (current_batch: 1) shows resume message.
    * Test clicking "Resume" loads current batch prompt.
    * Test with no progress (current_batch: 0) starts from batch 1 (no resume message).
  * Validation:
    * Test batch size < 1000 shows validation error.
    * Test batch size >= 1000 allows regeneration.
  * Edge cases:
    * Test changing batch size to exact remaining headings (1 batch remaining).
    * Test changing batch size to larger than remaining headings (1 batch, includes all).
* Suggested locations:
  * `vulcanlab_ui/src/app/simple-conversion/manual/[work_id]/__tests__/page.test.tsx` (extend existing tests)
* Mocking/fakes needed:
  * Mock fetch calls to batched API endpoints with query params.
  * Mock batch status response with varying current_batch values.

## Acceptance criteria (checklist)

* [ ] Input field for batch size added to batched workflow UI.
* [ ] "Regenerate Prompt" button added and functional.
* [ ] Changing batch size and clicking "Regenerate Prompt" fetches new prompt with updated batch size.
* [ ] Total batches recalculates after batch size change.
* [ ] Resume detection on page load shows message for in-progress workflows.
* [ ] Clicking "Resume" loads current batch prompt and continues workflow.
* [ ] Validation prevents batch size < 1000.
* [ ] All unit tests pass.

## Manual verification

* Steps:
  * Upload markdown file with 12,000 headings.
  * Navigate to `/simple-conversion/manual/{work_id}`.
  * Verify "Batch Size (Headings)" input shows 5000.
  * Change batch size to 7000.
  * Click "Regenerate Prompt".
  * Verify total batches updates from 3 to 2.
  * Verify new prompt displays with heading range "1-7000".
  * Submit batch 1 with valid response.
  * Close browser tab.
  * Reopen `/simple-conversion/manual/{work_id}`.
  * Verify resume message: "Resume from Batch 2 of 2".
  * Click "Resume" button.
  * Verify UI loads batch 2 prompt.
  * Change batch size to 5000 for batch 2.
  * Click "Regenerate Prompt".
  * Verify total batches updates (may remain 2 if 5000 fits remaining 5000 headings).
  * Submit batch 2 and verify completion.
  * Test edge case: Upload file with 6000 headings.
  * Start with batch size 5000 (2 batches).
  * After batch 1, change batch size to 10000.
  * Verify total batches updates to 1 (last batch includes all remaining).
* Expected results:
  * Batch size input allows user to adjust batch size.
  * "Regenerate Prompt" fetches new prompt with updated size.
  * Total batches recalculates correctly.
  * Resume detection works after browser close/refresh.
  * Resume message displays for in-progress workflows.
  * Clicking "Resume" continues from current batch.
  * Validation prevents invalid batch sizes.

## Notes

* Requirements covered: R5 (resume after browser close), R11 (dynamic batch size adjustment).
* Batch size recalculation formula: `total_batches = ceil((total_headings - headings_processed_so_far) / new_batch_size) + current_batch_index`.
* Resume functionality depends on batch progress persistence in database (already implemented in T02 and T03).
* "Start Over" button (optional): If implemented, should call DELETE endpoint to remove batch progress record and restart from batch 0. Can be deferred if not critical.
* Edge case: If user changes batch size to very large value (e.g., 50000) for a 12000 heading file on batch 2, remaining headings fit in 1 batch, so total_batches becomes current_batch + 1.
