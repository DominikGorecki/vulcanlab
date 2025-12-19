# Ticket: implementation-of-standardized-ui-components-across-all-pages.T02 - Batch 2: Corpus Management

## Source

* Spec: documentation/work/implementation-of-standardized-ui-components-across-all-pages.spec.md
* Patterns: documentation/patterns.md

## Goal

* Standardize the Corpus listing and detail pages.
* Implement `DataTable` with sorting and standardized `StatusBadge` for corpus items.
* Migrate corpus creation and edit forms to `react-hook-form`.

## Scope

### In scope

* `src/app/corpus/page.tsx`: Refactor listing to use `PageHeader`, `DataTable`, and `usePageData`.
* `src/app/corpus/[id]/page.tsx`: Refactor detail view to use `StickyDetailHeader` and `PageErrorState`.
* Corpus-specific modals or forms: Replace with `FormField` and connect to `react-hook-form`.
* Implement `ConfirmDialog` for corpus deletion.

### Out of scope

* File upload logic refactors (unless affecting UI state).
* RAG or Conversion page updates.

## Dependencies

* Depends on: T01
* Unblocks: T05

## Implementation plan

* Refactor `src/app/corpus/page.tsx`:
    * Define `DataTableColumn<Corpus>` definitions with sorting enabled for name/date.
    * Replace inline status logic with `StatusBadge` and a shared `corpusStatusConfig`.
* Refactor `src/app/corpus/[id]/page.tsx`:
    * Replace back navigation with `StickyDetailHeader`.
    * Use `usePageData` for fetching corpus metadata and associated statistics.
* Update corpus forms (New/Edit):
    * Standardize layout with `FormField` and `react-hook-form`.
* Patterns to apply:
    * DataTable - Generic tables with configurable columns.
    * StatusBadge - Universal status indicators.
    * StickyDetailHeader - Detail page headers.

## Unit tests (required)

* Add tests for:
    * `CorpusPage`: Verify `DataTable` renders the correct number of rows from mocked API.
    * `CorpusPage`: Verify clicking a row triggers navigation to `[id]`.
    * `CorpusDetailPage`: Verify `StickyDetailHeader` displays the correct corpus title.
* Suggested locations:
    * `src/app/corpus/__tests__/page.test.tsx`
    * `src/app/corpus/[id]/__tests__/page.test.tsx`
* Mocking/fakes needed:
    * API mock for `/api/v1/corpus`.

## Acceptance criteria (checklist)

* [ ] Corpus list uses `DataTable` with working sort.
* [ ] Corpus status displays using `StatusBadge`.
* [ ] Corpus detail page uses `StickyDetailHeader`.
* [ ] Deletion uses `ConfirmDialog`.
* [ ] All corpus-related unit tests pass.

## Manual verification

* Steps:
    * View corpus list, click column headers to sort.
    * Open a corpus detail page and verify the sticky header follows on scroll.
    * Delete a corpus item and verify the `ConfirmDialog` appearance.
* Expected results:
    * Visual and functional parity with the original implementation but using standardized components.

## Notes

* Requirements covered: R3, R4, R5, R8, R10, R17
