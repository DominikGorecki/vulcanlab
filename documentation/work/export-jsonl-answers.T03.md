# Ticket: export-jsonl-answers.T03 - Frontend Export Button

## Source

* Spec: documentation/work/export-jsonl-answers.spec.md
* Patterns: documentation/patterns.md

## Goal

* Add an "Export JSONL" button to the experiment details page next to the existing "Export CSV" button.
* Trigger file download when clicked.
* Ensure consistent styling and positioning with existing export button.

## Scope

### In scope

* Add "Export JSONL" button to the experiment details page (`vulcanlab_ui/src/app/eval/[id]/page.tsx`).
* Button click handler to initiate download from the API endpoint.
* Consistent styling with existing CSV export button.
* Handle loading and error states gracefully.

### Out of scope

* Backend implementation (T01, T02).
* Custom styling beyond matching existing button.
* Advanced features like progress indicators or cancel functionality.

## Dependencies

* Depends on: T02 (API endpoint must exist)
* Unblocks: None (final ticket)

## Implementation plan

* Open `vulcanlab_ui/src/app/eval/[id]/page.tsx` (or the relevant experiment details component).
* Locate the existing "Export CSV" button (likely in `StickyDetailHeader` or action area).
* Add a new "Export JSONL" button next to it with the same styling pattern.
* Implement click handler:
    * Construct URL: `/api/v1/eval/experiments/{id}/export-jsonl`.
    * Use `window.location.href = url` or create an anchor element and trigger click for download.
    * Optionally, use `fetch()` with blob handling for better error control.
* Add loading state while download initiates (optional but recommended).
* Add error handling: show toast or error message if download fails.
* Ensure button is only shown when experiment data is loaded.
* Patterns to apply:
    * Frontend Page Lifecycle - Use existing page data and state patterns.
    * Component Composition Rules - Props-in, events-out; consistent styling.
    * Standard Layout Hierarchy - Detail pages use `StickyDetailHeader` + action buttons.
* Deviations (if any):
    * None.

## Unit tests (required)

* Add tests for:
    * Button rendering: Verify "Export JSONL" button is present on experiment details page.
    * Click handler: Mock fetch/download, verify correct URL is called.
    * Error handling: Simulate failed download, verify error message is shown.
    * Button state: Verify button is disabled or hidden when appropriate (e.g., no experiment data).
* Suggested locations:
    * Add to existing frontend test file for experiment details page, or create `vulcanlab_ui/src/app/eval/[id]/page.test.tsx`.
* Mocking/fakes needed:
    * Mock `fetch` or `window.location.href` for download simulation.
    * Mock experiment data context.

## Acceptance criteria (checklist)

* [ ] "Export JSONL" button is visible on the experiment details page.
* [ ] Button is positioned next to the existing "Export CSV" button.
* [ ] Button styling matches the CSV export button.
* [ ] Clicking the button initiates a download from `/api/v1/eval/experiments/{id}/export-jsonl`.
* [ ] Downloaded file has the correct filename: `experiment_{id}_answers.jsonl`.
* [ ] Error states are handled gracefully (e.g., network error shows message).
* [ ] Unit tests verify button rendering and click behavior.
* [ ] All unit tests pass.

## Manual verification

* Steps:
    * Start the frontend development server: `cd vulcanlab_ui && npm run dev`.
    * Navigate to an experiment details page: `/eval/1`.
    * Verify the "Export JSONL" button appears next to the "Export CSV" button.
    * Click the "Export JSONL" button.
    * Verify browser downloads a file named `experiment_1_answers.jsonl`.
    * Open the downloaded file in a text editor.
    * Verify each line is valid JSON with `prompt_text`, `answer_x`, `answer_y` fields.
* Expected results:
    * Button is visible and styled consistently.
    * File downloads successfully.
    * File content is valid JSONL format.

## Notes

* Requirements covered: R5 (filename), partial R4 (endpoint called from frontend).
* Use the same download pattern as the CSV export button for consistency.
* Consider using a library like `file-saver` if more complex download handling is needed, but simple `window.location.href` should suffice.
* Ensure button is theme-aware (works in both light and dark mode).
* Use `useCallback` to memoize the click handler if needed to avoid re-renders.
