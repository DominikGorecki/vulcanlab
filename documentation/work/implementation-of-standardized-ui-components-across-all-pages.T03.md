# Ticket: implementation-of-standardized-ui-components-across-all-pages.T03 - Batch 3: RAG Workflows

## Source

* Spec: documentation/work/implementation-of-standardized-ui-components-across-all-pages.spec.md
* Patterns: documentation/patterns.md

## Goal

* Standardize all pages within the RAG functional domain (`/rag`, `/rag/new`, `/rag/auto`, `/rag/[id]`).
* Implement complex `DataTable` definitions for RAG runs and results.
* Migrate RAG configuration forms to `react-hook-form`.

## Scope

### In scope

* `src/app/rag/page.tsx`: Refactor RAG run history to use `DataTable` and `PageHeader`.
* `src/app/rag/new/page.tsx` & `src/app/rag/auto/page.tsx`: Refactor configuration forms.
* `src/app/rag/[id]/page.tsx`: Refactor detailed RAG results and evaluation views.
* Standardize RAG status indicators using `StatusBadge`.
* Use `StatsCardGrid` for RAG performance metrics if applicable.

### Out of scope

* Refactoring the RAG algorithm or backend processing logic.
* Modifying the markdown viewer used for RAG context (stay with `MarkdownStickyViewer`).

## Dependencies

* Depends on: T01
* Unblocks: T05

## Implementation plan

* Refactor `src/app/rag/page.tsx`:
    * Create a unified `ragStatusConfig` mapping.
    * Implement `DataTable` with columns for run type, timestamp, and status.
* Refactor RAG configuration pages (`new`, `auto`):
    * Move inline state management to `react-hook-form`.
    * Standardize parameters (e.g., Temperature, Top-P) with `FormField`.
* Refactor `src/app/rag/[id]/page.tsx`:
    * Replace manual tab/loading logic with `usePageData` and `DataTable` for individual retrieval results.
    * Use `StickyDetailHeader` for the run header.
* Patterns to apply:
    * usePageData - For multi-step fetching in RAG results.
    * StatsCardGrid - For summary metrics.

## Unit tests (required)

* Add tests for:
    * `RagPage`: Verify `usePageData` correctly handles the long-running fetch lifecycle.
    * `RagNewPage`: Verify form validation for required corpus selection.
    * `RagResultPage`: Verify sorting on evaluation metrics in the results table.
* Suggested locations:
    * `src/app/rag/__tests__/page.test.tsx`
    * `src/app/rag/[id]/__tests__/page.test.tsx`
* Mocking/fakes needed:
    * API mock for `/api/v1/rag` endpoints.

## Acceptance criteria (checklist)

* [x] RAG run list uses `DataTable` and `StatusBadge`.
* [x] RAG creation forms use `FormField` and `react-hook-form`.
* [x] RAG result detail uses `StickyDetailHeader`.
* [x] All RAG functional domain unit tests pass.

## Manual verification

* Steps:
    * Navigate through the RAG result history.
    * Create a new RAG run and check validation messages.
    * View a specific RAG run result and check column sorting in context results.
* Expected results:
    * Interactivity matches original but with more robust state handling via `usePageData`.

## Notes

* Requirements covered: R3, R4, R7, R8, R10, R13
* RAG pages are high-complexity; pay attention to `DataTable` row click handlers for deep linking.
