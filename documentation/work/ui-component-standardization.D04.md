# Ticket: ui-component-standardization.T04 - Data Display Components

## Source

* Spec: documentation/work/ui-component-standardization.spec.md
* Patterns: documentation/patterns.md

## Goal

* Create DataTable and StatusBadge components for standardized data display
* Enable type-safe table rendering with configurable columns and sorting
* Provide universal status badge component with flexible styling

## Scope

### In scope

* Implement DataTable generic component with TypeScript generics
* Support configurable columns with custom cell renderers
* Support optional sorting functionality per column
* Support optional row click handlers
* Support loading state and empty state in DataTable
* Implement StatusBadge component with configurable status mappings
* Integration with useTable hook for sorting state
* TypeScript prop interfaces with JSDoc comments
* Unit tests for both components
* Markdown documentation for both components

### Out of scope

* Server-side pagination or filtering
* Virtual scrolling for large datasets
* Column resizing or drag-and-drop
* Multi-select with checkboxes
* Export functionality
* Advanced table features (grouping, nested rows)

## Dependencies

* Depends on: T01 (useTable hook), T02 (EmptyState component)
* Unblocks: Future page migrations that use tables

## Implementation plan

* Create DataTable component:
  * Create vulcanlab_ui/src/components/data-table.tsx
  * Add "use client" directive
  * Define DataTableColumn<TData> interface (key, header, cell, sortable, className)
  * Define DataTableProps<TData> interface (data, columns, onRowClick, loading, emptyState, className)
  * Use existing Table primitives from vulcanlab_ui/src/components/ui/table.tsx
  * Integrate useTable hook for sorting state management
  * Render table header with column headers, add sort indicators for sortable columns
  * Render table body with rows, call cell renderer for each column
  * Handle onRowClick if provided (add cursor-pointer styling)
  * Show PageLoadingState when loading is true
  * Show EmptyState when data array is empty and not loading
  * Apply className to table container
  * Add JSDoc comments with usage example
* Create StatusBadge component:
  * Create vulcanlab_ui/src/components/status-badge.tsx
  * Add "use client" directive
  * Define StatusConfig interface (label, variant, icon optional)
  * Define StatusBadgeProps interface (status, statusConfig, className)
  * Look up status in statusConfig to get label, variant, and optional icon
  * Render Badge component from vulcanlab_ui/src/components/ui/badge.tsx
  * Apply variant styling (success, warning, error, info, default)
  * Render optional icon alongside label
  * Apply className to badge
  * Add JSDoc comments with usage example
* Write component documentation:
  * Create data-table.md with usage examples showing basic table and sortable table
  * Create status-badge.md with usage example showing status config mapping
* Write unit tests:
  * Test DataTable renders columns correctly
  * Test DataTable renders rows with cell renderers
  * Test DataTable handles empty data with EmptyState
  * Test DataTable shows loading state
  * Test DataTable sorting integration with useTable hook
  * Test DataTable row click handler is called
  * Test DataTable applies className
  * Test StatusBadge renders correct label and variant based on status
  * Test StatusBadge renders icon when provided in config
  * Test StatusBadge applies className
  * Test StatusBadge handles unknown status gracefully
* Patterns to apply:
  * Frontend Stack - Next.js, TypeScript, TailwindCSS, Radix UI (Table, Badge)
  * Component Organization - Components in vulcanlab_ui/src/components/
  * TypeScript Conventions - Use generics for type safety (DataTable<TData>)
  * File Naming - kebab-case for component files
  * Composition - Build on existing Table and Badge primitives
* Deviations (if any):
  * None - fully compliant with patterns.md

## Unit tests (required)

* Add tests for:
  * DataTable: renders table headers from columns, renders table rows from data, calls cell renderer for each cell, shows EmptyState when data is empty, shows PageLoadingState when loading is true, calls onRowClick when row is clicked, applies sortable column styling, integrates with useTable for sorting, applies className
  * StatusBadge: renders label from statusConfig, applies correct variant styling, renders icon when provided, applies className, handles unknown status with default variant, falls back gracefully when statusConfig is missing status key
* Suggested locations:
  * vulcanlab_ui/src/components/data-table.test.tsx
  * vulcanlab_ui/src/components/status-badge.test.tsx
* Mocking/fakes needed:
  * Mock useTable hook for DataTable tests
  * Mock icon components for StatusBadge tests
  * Mock test data arrays with various data shapes

## Acceptance criteria (checklist)

* [ ] DataTable component implemented with TypeScript generics and JSDoc
* [ ] DataTable supports configurable columns with cell renderers
* [ ] DataTable supports optional sorting via useTable hook integration
* [ ] DataTable supports optional row click handlers
* [ ] DataTable shows loading state and empty state correctly
* [ ] DataTable uses existing Table primitives from ui/
* [ ] StatusBadge component implemented with TypeScript types and JSDoc
* [ ] StatusBadge accepts configurable status mappings
* [ ] StatusBadge supports variants (success, warning, error, info, default)
* [ ] StatusBadge uses existing Badge component from ui/
* [ ] Both components support className prop
* [ ] Both components have "use client" directive
* [ ] Markdown documentation created for both components
* [ ] Unit tests written with at least 80% coverage
* [ ] All tests pass
* [ ] TypeScript compilation passes with strict mode
* [ ] Components tested manually with 50-100 row dataset for performance

## Manual verification

* Steps:
  * Create test page with DataTable showing 10 rows of sample data
  * Create test page with DataTable showing 100 rows to test performance
  * Add sortable columns and test sorting ascending/descending
  * Add row click handler and verify it's called with correct row data
  * Test DataTable with empty data array to see EmptyState
  * Test DataTable with loading prop to see PageLoadingState
  * Create test showing StatusBadge with different statuses (completed, pending, failed, processing)
  * Toggle between light and dark themes
  * Test on mobile, tablet, desktop viewports
* Expected results:
  * DataTable renders rows correctly with proper spacing and borders
  * Sorting works correctly in both directions
  * Row click highlights row and calls handler
  * Empty state and loading state display correctly
  * DataTable handles 100 rows without noticeable performance issues
  * StatusBadge displays correct colors and icons for each status
  * Components render correctly in both themes
  * Table is horizontally scrollable on mobile when needed

## Notes

* Requirements covered: R3, R4, R5, R14, R16, R17, R18, R19, R20
* DataTable is one of the most complex components - careful testing needed
* DataTable will be used in corpus page, RAG page, simple-conversion page, and others
* StatusBadge will be used in DataTable cells and other status displays
* Consider using React.memo for DataTable to prevent unnecessary re-renders with large datasets
* Cell renderer function allows full flexibility for custom cell content (links, buttons, badges, etc.)
* DataTable should handle at least 100 rows efficiently as per non-functional requirements
* Test with various data types in cells (strings, numbers, dates, React components)
