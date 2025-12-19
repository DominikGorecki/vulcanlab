# Ticket: implementation-of-standardized-ui-components-across-all-pages.T04 - Batch 4: Simple Conversion

## Source

* Spec: documentation/work/implementation-of-standardized-ui-components-across-all-pages.spec.md
* Patterns: documentation/patterns.md

## Goal

* Standardize the Simple Conversion history, manual, and automatic pages.
* Replace custom conversion status tracking with `DataTable` and `StatusBadge`.
* Migrate conversion upload and parameter forms to `react-hook-form`.

## Scope

### In scope

* `src/app/simple-conversion/page.tsx`: Listing view.
* `src/app/simple-conversion/history/page.tsx`: Detailed history tracking.
* `src/app/simple-conversion/manual/page.tsx` & `/automatic/page.tsx`: Upload and trigger forms.
* Standardize conversion status badges (pending, processing, failed, completed).
* Implement `PageHeader` with conversion-specific actions.

### Out of scope

* Refactoring the PDF-to-Markdown conversion worker.
* Changes to file storage or download URLs.

## Dependencies

* Depends on: T01
* Unblocks: T05

## Implementation plan

* Refactor `src/app/simple-conversion/page.tsx`:
    * Implement `DataTable` for the primary conversion list.
    * Use `usePageData` with a retry mechanism for failed fetches.
* Refactor Conversion History:
    * Replace manual grid/list layouts with `DataTable`.
    * Standardize timestamp formatting in columns.
* Refactor Manual/Automatic Upload pages:
    * Use `FormField` for file and parameter inputs.
    * Connect to `react-hook-form` and handle async submission states.
* Patterns to apply:
    * StatusBadge - With specialized icons for conversion steps.
    * PageErrorState - Highlighting specific conversion failure errors.

## Unit tests (required)

* Add tests for:
    * `SimpleConversionPage`: Verify `DataTable` displays items correctly.
    * `ManualConversionPage`: Verify form error state when no file is selected.
    * `HistoryPage`: Verify sorting by conversion duration/id.
* Suggested locations:
    * `src/app/simple-conversion/__tests__/page.test.tsx`
* Mocking/fakes needed:
    * API mock for `/api/v1/simple-conversion`.

## Acceptance criteria (checklist)

* [ ] Conversion list uses `DataTable` and `StatusBadge`.
* [ ] Upload forms use `FormField` and `react-hook-form`.
* [ ] Page transitions use `PageLoadingState`.
* [ ] All conversion-related unit tests pass.

## Manual verification

* Steps:
    * Trigger a manual conversion and observe the status update (if polling exists).
    * Navigate to history and search/sort through conversion logs.
* Expected results:
    * Unified look and feel with the rest of the application.

## Notes

* Requirements covered: R1, R2, R3, R4, R6, R9
