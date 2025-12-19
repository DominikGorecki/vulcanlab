# Ticket: implementation-of-standardized-ui-components-across-all-pages.T05 - Batch 5: Processing Pages & Final Cleanup

## Source

* Spec: documentation/work/implementation-of-standardized-ui-components-across-all-pages.spec.md
* Patterns: documentation/patterns.md

## Goal

* Standardize the remaining 15+ processing and utility pages (`/chunk`, `/vec`, `/cleanup`, `/sanitization`, `/conv`).
* Perform final cleanup by deleting deprecated components and resolving any remaining legacy UI patterns.
* Ensure all 39 pages are fully integrated with the shared library.

## Scope

### In scope

* Refactoring all pages in:
    * `/chunk` (chunking configuration and results)
    * `/vec` (vectorization status)
    * `/cleanup` (data cleanup utilities)
    * `/sanitization` (data sanitization pipeline)
    * `/conv` (conversion utilities)
* Deletion of `src/components/ConfirmDeleteModal.tsx`.
* Deletion of `src/components/ErrorModal.tsx`.
* Resolving any "TODO" or "Legacy" comments introduced during the migration.

### Out of scope

* Backend database cleanups.
* Non-UI files in `vulcanlab_ui`.

## Dependencies

* Depends on: T01, T02, T03, T04
* Unblocks: none

## Implementation plan

* Iterate through the remaining directories in `src/app` and apply the migration pattern:
    * `usePageData` for fecthing.
    * `PageHeader` for titles.
    * `DataTable` for summaries.
    * `FormField` for configuration parameters.
* Audit all imports in `vulcanlab_ui` to ensure no references to `ConfirmDeleteModal` or `ErrorModal` remain.
* Delete the deprecated files and their associated tests.
* Perform a final styling pass to ensure Tailwind CSS v4 consistency across all 39 pages.
* Patterns to apply:
    * Full adoption of the Shared Component Library index.

## Unit tests (required)

* Add tests for:
    * Every remaining page receives at least one unit test verifying the `PageHeader` or `DataTable` presence.
    * Verification that `ConfirmDialog` is now used globally (grep check).
* Suggested locations:
    * Respective `__tests__` folders for each processing domain.
* Mocking/fakes needed:
    * API mocks for processing endpoints.

## Acceptance criteria (checklist)

* [ ] All remaining processing pages (Batch 5) use standardized components.
* [ ] `ConfirmDeleteModal.tsx` is deleted.
* [ ] `ErrorModal.tsx` is deleted.
* [ ] No references to legacy components exist in the codebase.
* [ ] All 39 pages pass their respective unit tests.

## Manual verification

* Steps:
    * Smoke test of the utility pages (Chunking, Vectorization, Cleanup).
    * Verify that deletion prompts everywhere use the new `ConfirmDialog` layout.
* Expected results:
    * 100% component library adoption.
    * Zero technical debt related to the standardized UI patterns.

## Notes

* Requirements covered: R1 through R20 (Final validation)
* This is the "closing" ticket for the entire migration effort.
