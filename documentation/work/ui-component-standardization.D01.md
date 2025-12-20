# Ticket: ui-component-standardization.T01 - Foundation Hooks and Dependencies

## Source

* Spec: documentation/work/ui-component-standardization.spec.md
* Patterns: documentation/patterns.md

## Goal

* Install react-hook-form dependency for form validation
* Create three foundational custom hooks (useModal, usePageData, useTable) that will be used across all components
* Establish the hooks directory structure with proper exports and TypeScript types

## Scope

### In scope

* Install react-hook-form as a dependency in vulcanlab_ui
* Create vulcanlab_ui/src/hooks/ directory
* Implement useModal hook for modal state management
* Implement usePageData hook for data fetching with loading/error/retry states
* Implement useTable hook for table sorting state
* Create index.ts export file for hooks
* Write unit tests for all three hooks
* TypeScript strict mode compliance with full type definitions and JSDoc comments

### Out of scope

* Component implementations (covered in later tickets)
* Integration testing
* Hook usage examples in actual pages
* Advanced features like polling or caching in usePageData
* Multi-select or pagination in useTable

## Dependencies

* Depends on: none
* Unblocks: T02, T03, T04, T05, T06

## Implementation plan

* Install react-hook-form: Run `npm install react-hook-form` in vulcanlab_ui directory
* Create hooks directory: Create vulcanlab_ui/src/hooks/ directory structure
* Implement useModal hook:
  * Create vulcanlab_ui/src/hooks/use-modal.ts
  * Implement state management for open/close/toggle with boolean state
  * Return typed object with isOpen, open, close, toggle functions
  * Add JSDoc comments explaining usage
* Implement usePageData hook:
  * Create vulcanlab_ui/src/hooks/use-page-data.ts
  * Accept generic type parameter TData for type safety
  * Accept fetchFn and optional options (autoFetch, onError)
  * Implement loading, error, success state management with useState
  * Implement refetch functionality
  * Use useEffect for auto-fetch when autoFetch is true
  * Handle errors gracefully and call onError callback if provided
  * Add JSDoc comments with usage examples
* Implement useTable hook:
  * Create vulcanlab_ui/src/hooks/use-table.ts
  * Accept generic type parameter TData
  * Accept data array, defaultSortKey, defaultSortDirection
  * Implement sorting state management with useState
  * Implement handleSort function that toggles direction and updates sortKey
  * Compute sortedData using useMemo with sorting logic
  * Return sortedData, sortKey, sortDirection, handleSort
  * Add JSDoc comments
* Create index exports: Create vulcanlab_ui/src/hooks/index.ts that exports all hooks
* Write unit tests: Create test files for each hook with happy path and error scenarios
* Patterns to apply:
  * TypeScript Conventions - PascalCase for types, camelCase for hook names and functions
  * File Naming - kebab-case for hook files (use-modal.ts, use-page-data.ts, use-table.ts)
  * Component Organization - Hooks in vulcanlab_ui/src/hooks/ as specified in patterns.md
* Deviations (if any):
  * react-hook-form dependency addition - Not currently in project - Aligns with shadcn/ui form patterns, lightweight validation approach

## Unit tests (required)

* Add tests for:
  * useModal: initial state is closed, open/close/toggle work correctly, accepts defaultOpen parameter
  * usePageData: handles loading state, handles success state with data, handles error state, refetch works, autoFetch triggers on mount, onError callback is called on error, handles fetchFn rejection
  * useTable: returns sorted data in ascending order, toggles to descending on second click, handles unsortable columns, handles empty data array, preserves original order when sortKey is null
* Suggested locations:
  * vulcanlab_ui/src/hooks/use-modal.test.ts
  * vulcanlab_ui/src/hooks/use-page-data.test.ts
  * vulcanlab_ui/src/hooks/use-table.test.ts
* Mocking/fakes needed:
  * Mock async fetchFn for usePageData tests (resolved and rejected promises)
  * Mock data arrays for useTable tests

## Acceptance criteria (checklist)

* [ ] react-hook-form installed and added to package.json dependencies
* [ ] vulcanlab_ui/src/hooks/ directory created
* [ ] useModal hook implemented with TypeScript types and JSDoc
* [ ] usePageData hook implemented with generic type support and JSDoc
* [ ] useTable hook implemented with generic type support and JSDoc
* [ ] All hooks exported from vulcanlab_ui/src/hooks/index.ts
* [ ] Unit tests written for all hooks with at least 80% coverage
* [ ] All tests pass
* [ ] TypeScript compilation passes with strict mode
* [ ] No any types used without justification

## Manual verification

* Steps:
  * Run npm install in vulcanlab_ui directory
  * Verify react-hook-form appears in package.json dependencies
  * Run TypeScript compiler to verify no errors
  * Run unit tests: npm test (or appropriate test command)
  * Import hooks in a test file to verify exports work correctly
* Expected results:
  * react-hook-form version appears in package.json
  * All TypeScript files compile without errors
  * All unit tests pass
  * Hooks can be imported via `import { useModal, usePageData, useTable } from '@/hooks'`

## Notes

* Requirements covered: R13, R14, R15, R17, R18
* usePageData hook will be used by PageLoadingState and PageErrorState components
* useTable hook will be used by DataTable component
* useModal hook will be used by ConfirmDialog and other modal patterns
* Consider using @testing-library/react-hooks for testing custom hooks
* Follow React hooks rules (start with 'use', don't call conditionally)
* These hooks establish patterns for state management that will reduce boilerplate in all page components
