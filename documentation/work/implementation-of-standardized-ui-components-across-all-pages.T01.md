# Ticket: implementation-of-standardized-ui-components-across-all-pages.T01 - Batch 1: Core, Settings, and Global Error Boundary

## Source

* Spec: documentation/work/implementation-of-standardized-ui-components-across-all-pages.spec.md
* Patterns: documentation/patterns.md

## Goal

* Migrate the root page, `/init`, and `/settings` pages to the shared component library.
* Implement a global Error Boundary using `PageErrorState` to capture and display unhandled client-side crashes consistently.
* Establish the pattern for `usePageData` and `react-hook-form` migration for subsequent batches.

## Scope

### In scope

* `src/app/page.tsx`: Refactor to use `PageHeader`, `DataTable` (if applicable), and `usePageData`.
* `src/app/init/page.tsx`: Refactor to use `PageHeader`, `FormField`, and `react-hook-form`.
* `src/app/settings/page.tsx` (and tabs): Refactor to use `PageHeader`, `FormField`, and `usePageData` for settings fetching.
* Create a `GlobalErrorBoundary` component in `src/components/` and wrap the root layout in `src/app/layout.tsx`.
* Update `ConfirmDialog` usage for any deletions in these pages.

### Out of scope

* Migrating any pages outside of the Core/Settings domain.
* Backend changes for settings persistence.

## Dependencies

* Depends on: Phase 1 (Shared Component Library established)
* Unblocks: T02, T03, T04, T05

## Implementation plan

* Create `src/components/global-error-boundary.tsx` using `PageErrorState` and a standard React Error Boundary wrapper.
* Modify `src/app/layout.tsx` to include the `GlobalErrorBoundary` inside the provider stack.
* Refactor `src/app/page.tsx`:
    * Replace manual fetch/loading/error state with `usePageData`.
    * Replace manual layouts with `PageHeader`.
* Refactor `src/app/init/page.tsx`:
    * Implement `react-hook-form` with `Zod` validation (if schema exists).
    * Wrap inputs in `FormField`.
* Refactor `src/app/settings/page.tsx`:
    * Update individual tabs (e.g., `rag-config-tab.tsx`) to use standardized components.
* Patterns to apply:
    * Frontend Standard - Next.js App Router, Tailwind CSS v4.
    * Shared Component Library - PageHeader, PageLoadingState, PageErrorState, FormField.

## Unit tests (required)

* Add tests for:
    * `GlobalErrorBoundary`: Verify it renders `PageErrorState` when a child component throws.
    * `InitPage`: Verify `react-hook-form` validation blocks submission on empty fields.
    * `SettingsPage`: Verify `usePageData` successfully loads initial configurations.
* Suggested locations:
    * `src/app/__tests__/page.test.tsx`
    * `src/app/init/__tests__/page.test.tsx`
    * `src/app/settings/__tests__/page.test.tsx`
* Mocking/fakes needed:
    * API mock for `/api/v1/settings` and initialization endpoints.

## Acceptance criteria (checklist)

* [ ] Root page (`/`) uses `usePageData` and `PageHeader`.
* [ ] `/init` uses `FormField` and `react-hook-form`.
* [ ] `/settings` and its tabs use standardized components.
* [ ] Global Error Boundary captures a forced error and displays `PageErrorState`.
* [ ] All unit tests pass with mocked APIs.

## Manual verification

* Steps:
    * Navigate to `/init` and try to submit empty forms to see validation errors.
    * Force a rendering error in a component to verify the Global Error Boundary.
    * Check `/settings` list and detail views for layout consistency.
* Expected results:
    * Layout matches standardized design.
    * Error boundary displays a "Retry" or "Refresh" button.

## Notes

* Requirements covered: R1, R2, R5, R6, R7, R19
* `rag-config-tab.tsx` is a key component to update in this batch.
