# Title: Implementation of Standardized UI Components Across All Pages

## Summary

* Migrate 39 pages in `vulcanlab_ui` to use the shared component library established in Phase 1.
* Replace custom loading/error states, tables, status badges, and headers with standardized components (`PageLoadingState`, `PageErrorState`, `DataTable`, `StatusBadge`, `PageHeader`, `StickyDetailHeader`).
* Standardize data fetching using the `usePageData` hook across all functional domains.
* Implement `react-hook-form` validation using the `FormField` component in all user input forms.
* Clean up legacy UI components (`ConfirmDeleteModal.tsx`, `ErrorModal.tsx`) as they are replaced.
* Ensure UI consistency, maintainability, and responsiveness across the entire application.

## Problem / Context

* The application contains 39 pages with highly duplicated UI logic, leading to inconsistencies in look, feel, and behavior.
* Maintenance is difficult as bug fixes or design updates must be applied to dozens of files.
* Data fetching and error handling patterns vary between pages, making the developer experience fragmented.
* Legacy components like `ConfirmDeleteModal` and inline loading spinners exist alongside newer standards, creating technical debt.
* Several pages lack proper form validation or use inconsistent validation libraries.

## Goals

* Achieving 100% adoption of the shared component library across all pages.
* Eliminating duplicate UI logic for common patterns (loading, errors, tables).
* Standardizing the user experience for all data-driven views and forms.
* Improving codebase maintainability by reducing total lines of code and complexity in page components.
* Ensuring all forms follow `react-hook-form` patterns with clear feedback.

## Non-goals (Strict)

* Redesigning the UX or visual identity of the application (stick to existing standards).
* Implementing new backend API endpoints or modifying data models.
* Adding new business features during the migration (feature-parity migration only).
* Implementing advanced UI features (e.g., drag-and-drop, complex animations) not already present.

## Scope

### In scope

* **Refactoring 39 Page Components**: Updating all files in `src/app` to use shared components and hooks.
* **Functional Domain Batches**:
    * **Batch 1: Core & Settings**: Root page, `/init`, `/settings`.
    * **Batch 2: Corpus Management**: `/corpus` and details.
    * **Batch 3: RAG Workflows**: `/rag`, `auto`, `new`, and details.
    * **Batch 4: Simple Conversion**: `/simple-conversion`, `history`, `manual`, `automatic`.
    * **Batch 5: Retrieval & Processing**: `/chunk`, `/vec`, `/cleanup`, `/sanitization`, `/conv`.
* **Component Enhancement**: Extending shared components with new props where necessary for functional parity, ensuring backward compatibility.
* **Component Deletion**: Removing `ConfirmDeleteModal.tsx` and `ErrorModal.tsx` once references reach zero.
* **Documentation Update**: Adding specific page migration notes to `documentation/work/ui-component-library-guide.md` if unique patterns are discovered.

### Out of scope

* Migrating to Server Actions (continue using current API fetching patterns).
* Introducing Global State Management (e.g., Redux, Zustand) if not already used.
* Refactoring the CSS architecture (stay with Tailwind CSS v4).

## Requirements (Functional)

* R1: Every page must use `PageLoadingState` for initial data loading.
* R2: Every page must use `PageErrorState` for data fetching failures, including `onRetry` support where applicable.
* R3: All tabular data must be rendered using `DataTable` with typed `DataTableColumn` definitions.
* R4: All status indicators must use `StatusBadge` with a standardized `StatusConfig` map.
* R5: All pages must include either `PageHeader` (list views) or `StickyDetailHeader` (detail views).
* R6: All forms must be migrated to `react-hook-form` using the `FormField` component for layout and validation display.
* R7: All data-fetching logic should be moved to the `usePageData` hook, except where logic is too unique to reasonably fit.
* R8: Destructive actions must use `ConfirmDialog` instead of legacy modals or generic `window.confirm`.

## Requirements (Non-functional)

* Performance:
    * Migrated pages should have equal or better performance compared to their original implementations.
    * Avoid prop-drilling by leveraging the component composition patterns defined in the library.

* Reliability:
    * Each migrated page must have a basic unit test mocking the API and verifying the core UI states (loading, error, data).

* Security / Privacy:
    * Ensure `FormField` correctly masks sensitive inputs (e.g., API keys) and doesn't leak validation errors to external logs.

* Observability:
    * Retain existing logging for data fetching errors within the `usePageData` error callbacks.

## Proposed Solution (High-level)

* Follow a domain-by-domain migration strategy to manage risk and complexity.
* For each page:
    1. Analyze the current implementation for loading, error, and data display patterns.
    2. Extract data fetching into `usePageData`.
    3. Replace custom table implementations with `DataTable` and appropriate column definitions.
    4. Wrap form inputs in `FormField` and connect to `react-hook-form`.
    5. Update headers and navigation links to use `PageHeader` or `StickyDetailHeader`.
    6. Verify functional parity with the original page.
* If a standardized component lacks a required feature, enhance it in `src/components/` with optional props and default values to maintain backward compatibility.

## Interfaces / APIs / Contracts

* Components will continue to use the established interfaces in `vulcanlab_ui/src/components/index.ts`.
* Page components will consume existing API schemas as defined in their current implementations.

## Data Model / Storage

Not applicable. This is a UI-only migration.

## UX / Workflows

* The user will see a more consistent UI across the entire application.
* Standardized loading spinners and error messages will replace fragmented indicators.
* Table interactions (sorting, row clicks) will behave identically on every page.
* Form validation feedback will be immediate and visually consistent.

## Testing Plan

* Unit tests:
    * Create/Update unit tests for each page in its respective `__tests__` directory.
    * Verify that `usePageData` is called with the correct parameters.
    * Verify that `DataTable` receives the expected data and columns.
* Manual test plan:
    * Verify mobile responsiveness for all migrated pages.
    * Verify theme consistency (light/dark mode) for all components.
    * Exercise all primary user actions (create, update, delete, search) on each page.

## Acceptance Criteria (Checklist)

* [ ] Batch 1: Core & Settings migrated and verified.
* [ ] Batch 2: Corpus functional domain migrated and verified.
* [ ] Batch 3: RAG functional domain migrated and verified.
* [ ] Batch 4: Simple Conversion functional domain migrated and verified.
* [ ] Batch 5: Processing & Remaining pages migrated and verified.
* [ ] `ConfirmDeleteModal.tsx` deleted.
* [ ] `ErrorModal.tsx` deleted.
* [ ] All 39 pages pass unit tests with mocked APIs.
* [ ] Standardized components enhanced for parity where necessary (backwards compatible).

## Rollout / Migration Plan

* **Phase 1: Batch 1 (Core & Settings)**: Low-risk pages to establish the workflow.
* **Phase 2: Batch 2 & 3 (Corpus & RAG)**: High-impact pages with complex tables and states.
* **Phase 3: Batch 4 & 5 (Conversion & Remaining)**: Lower-frequency pages and cleanup.
* Incremental PRs: Each domain batch (or significant page) should be a separate PR.

## Risks and Alternatives

* Risks:
    * **Scope Creep**: Wanting to fix bugs or add features while migrating. Mitigation: Strict "feature-parity only" rule.
    * **Breaking Changes**: Enhancing shared components might break Phase 1 pages if not done carefully. Mitigation: Strict backward compatibility checks.
    * **Test Complexity**: Mocking complex API flows for unit tests. Mitigation: Use helper utilities for common API mock patterns.

* Alternatives considered:
    * **Big Bang Migration**: Migrating all 39 pages in one commit. Rejected due to high risk of regression and review difficulty.
    * **Opt-in Migration**: Only migrating new pages. Rejected as it leaves the codebase in a permanent state of fragmentation and high technical debt.

## Patterns and Standards Alignment (from documentation/patterns.md)

* Patterns applied:
    * Frontend Standard: Next.js App Router, Tailwind CSS v4, Radix UI.
    * Shared Component Library: Using all components specified in section 4.
    * Forms: Mandatory `react-hook-form` integration.

## Implementation Notes (Non-binding)

* Look for "quick wins" in the `lib` folder if any API wrappers can be further standardized to work better with `usePageData`.
* Use the expansion/collapsibility of the `DataTable` and `FormField` to handle edge cases without bloating the component logic.

## Open Questions

* Q1: Are there any specific pages that require complex multi-part forms that might need a new specialized layout component?
* Q2: Should we implement a global error Boundary that uses `PageErrorState` for unhandled client-side crashes?
