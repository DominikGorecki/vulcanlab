# Ticket: chunked-manual-sanitization.T05 - Manual Page Batched Workflow UI (Basic Flow)

## Source

* Spec: documentation/work/chunked-manual-sanitization.spec.md
* Patterns: documentation/patterns.md

## Goal

* Modify manual workflow page to detect when batched workflow is needed and render batched UI instead of single-step.
* Implement basic batched workflow: display batch prompt, accept batch submission, progress through batches to completion.
* Provide "Batch N of M" progress indicator.
* Enable end-to-end manual batched sanitization for large files.

## Scope

### In scope

* Detection logic in `vulcanlab_ui/src/app/simple-conversion/manual/[work_id]/page.tsx` to check heading count against threshold.
* Conditional rendering: If heading count > batch_size_headings, render batched UI; else render single-step UI.
* Batched UI components:
  * Progress indicator showing "Batch N of M".
  * Prompt display card with batch-specific prompt.
  * Textarea for pasting LLM response.
  * Submit button for batch submission.
  * Automatic progression to next batch after successful submission.
  * Completion state when all batches done (reuse existing results display).
* Integration with batched API endpoints from T03.
* Unit tests for batched workflow UI logic.

### Out of scope

* Dynamic batch size adjustment (T06).
* Resume functionality (T06).
* Settings page (T04 - already done).
* Single-step workflow changes (must remain unchanged per R8).

## Dependencies

* Depends on: T03 (API endpoints), T04 (settings must be available)
* Unblocks: T06

## Implementation plan

* Open `vulcanlab_ui/src/app/simple-conversion/manual/[work_id]/page.tsx`.
* Add state for batched workflow mode:
  * `isBatchedWorkflow: boolean`.
  * `batchedStatus: BatchedStatusResponse | null`.
  * `currentBatchPrompt: BatchedPromptResponse | null`.
* On page load, after fetching work metadata:
  * Fetch batch status via `GET /api/simple-conversion/batched-status/{work_id}`.
  * If `batched_enabled: true`, set `isBatchedWorkflow: true` and load current batch prompt.
  * If `batched_enabled: false`, check heading count:
    * Fetch heading count from parsed_markdown or work metadata.
    * Load global `batch_size_headings` from config (via settings API or hardcoded fallback).
    * If heading count > batch_size_headings, set `isBatchedWorkflow: true` and fetch first batch prompt via `GET /api/simple-conversion/manual-prompt-batched/{work_id}`.
    * Else, use existing single-step workflow (no changes).
* Implement batched UI components (conditional render):
  * If `isBatchedWorkflow === true`:
    * Render progress indicator: "Batch {batch_index + 1} of {total_batches}".
    * Render batch info card: "Processing headings {heading_range}".
    * Render prompt display card (reuse existing prompt display from single-step).
    * Render textarea for LLM response (reuse existing).
    * Render submit button with label "Submit Batch {batch_index + 1}".
  * Else:
    * Render existing single-step UI (no changes).
* Implement batch submission handler:
  * On submit, call `POST /api/simple-conversion/manual-submit-batched/{work_id}` with LLM response.
  * If response `is_complete: false`, fetch next batch prompt via `GET /api/simple-conversion/manual-prompt-batched/{work_id}`.
  * Update UI to show next batch (clear textarea, update progress indicator).
  * If response `is_complete: true`, fetch results via existing results endpoint and show completion state (reuse existing results UI).
* Add error handling for invalid batch responses (display error message, block progression).
* Patterns to apply:
  * **Frontend Page Lifecycle** - Use `usePageData` hook for fetching batch status and prompts.
  * **Component Composition** - Reuse existing `Card`, `Textarea`, `Button`, `Alert` components.
  * **State Management** - Client component with `useState` for batch state.
* Deviations (if any):
  * None; follows established patterns.

## Unit tests (required)

* Add tests for:
  * Detection logic:
    * Test with heading count 4999 (renders single-step UI).
    * Test with heading count 5001 (renders batched UI).
    * Test with existing batched progress (resumes batched UI).
  * Batched UI rendering:
    * Test progress indicator shows "Batch 1 of 3".
    * Test prompt display shows correct batch prompt.
    * Test submit button label is "Submit Batch 1".
  * Batch submission:
    * Test submitting batch 1 fetches batch 2 prompt.
    * Test submitting final batch shows completion state.
    * Test submitting invalid response shows error message.
  * Single-step workflow unchanged:
    * Test with heading count < threshold renders existing UI.
    * Test existing single-step submit flow still works.
* Suggested locations:
  * `vulcanlab_ui/src/app/simple-conversion/manual/[work_id]/__tests__/page.test.tsx`
* Mocking/fakes needed:
  * Mock fetch calls to batched API endpoints.
  * Mock fetch calls to existing single-step endpoints.
  * Mock work metadata with varying heading counts.

## Acceptance criteria (checklist)

* [ ] Manual page detects heading count on load.
* [ ] If heading count > batch_size_headings, batched UI renders.
* [ ] If heading count <= batch_size_headings, single-step UI renders (unchanged).
* [ ] Batched UI shows "Batch N of M" progress indicator.
* [ ] Batched UI displays batch-specific prompt and heading range.
* [ ] User can paste LLM response and submit batch.
* [ ] After batch submission, UI automatically shows next batch prompt.
* [ ] After final batch submission, completion state displays with results.
* [ ] Invalid batch response displays error and blocks progression.
* [ ] Single-step workflow remains unchanged.
* [ ] All unit tests pass.

## Manual verification

* Steps:
  * Upload markdown file with 12,000 headings (use test fixture).
  * Navigate to `/simple-conversion/manual/{work_id}`.
  * Verify UI shows "Batch 1 of 3" progress indicator.
  * Verify prompt display shows batch prompt with heading range "1-5000".
  * Copy prompt, paste into external LLM, get valid JSON response.
  * Paste JSON response into textarea.
  * Click "Submit Batch 1".
  * Verify UI automatically updates to show "Batch 2 of 3".
  * Verify new prompt displayed with heading range "5001-10000".
  * Repeat for batch 2 and batch 3.
  * After submitting batch 3, verify completion state shows results with chunks.
  * Upload markdown file with 4000 headings.
  * Navigate to `/simple-conversion/manual/{work_id}`.
  * Verify single-step UI renders (no batch progress indicator).
  * Verify single-step workflow still works (paste response, submit, see results).
* Expected results:
  * Batched workflow renders for large files (>5000 headings).
  * Single-step workflow renders for small files (<=5000 headings).
  * Batched workflow progresses through all batches to completion.
  * Invalid responses show error messages.
  * Single-step workflow unchanged and functional.

## Notes

* Requirements covered: R1 (automatic detection), R2 (prompt generation), R5 (partial - basic progression), R6 (validation and error display), R7 (only for large files), R8 (single-step unchanged), R13 (completion proceeds to existing flow).
* Heading count source: Should come from `parsed_markdown` record (number of heading entries in condensed document).
* Threshold value: Load from config via settings API or use hardcoded fallback 5000 if API unavailable.
* Error display: Reuse existing `Alert` component with `variant="destructive"` for validation errors.
* Completion flow: After final batch, proceed to existing results display with chunks (no changes to results UI needed).
