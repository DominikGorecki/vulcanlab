# Title: UI Component Standardization and Shared Component Library

## Summary

* Extract duplicated UI patterns from 39 pages in vulcanlab_ui into a shared component library to reduce code duplication and improve maintainability
* Create 10+ reusable components for loading states, error states, data tables, status badges, forms, modals, and page layouts
* Implement custom React hooks for data fetching and common UI state management patterns
* Establish component documentation and usage guidelines in documentation/patterns.md
* Design components for backward compatibility allowing incremental page-by-page migration
* Integrate react-hook-form for lightweight form validation following shadcn/ui best practices

## Problem / Context

* The vulcanlab_ui codebase contains 39 page files with significant code duplication across common UI patterns
* Loading states are implemented 53+ times with nearly identical code across all pages
* Error states are duplicated 53+ times with similar patterns but inconsistent styling
* Data tables are reimplemented in at least 5 different pages with similar structure but subtle differences
* Status badge logic is duplicated in multiple pages with inline switch statements
* Form validation is implemented inconsistently across 10+ pages with different validation timing and error display patterns
* Modal workflows are created inline in pages, leading to large, complex page components
* Empty states, page headers, and stats cards follow similar patterns but lack a shared implementation
* Users experience inconsistent UI behavior across different pages (e.g., error display, loading indicators)
* Developers spend significant time reimplementing the same patterns when creating new pages
* Bug fixes and UX improvements must be applied to multiple locations instead of a single shared component
* The codebase is harder to maintain and test due to scattered implementations of the same functionality

**User Impact:**
* Inconsistent user experience across different sections of the application
* Slower development velocity for new features
* Higher likelihood of bugs due to duplicated code paths

**Business Impact:**
* Increased maintenance costs and technical debt
* Slower time-to-market for new features
* Reduced code quality and reliability

## Goals

* Reduce code duplication by extracting shared UI patterns into reusable components
* Improve UI consistency across all pages in the application
* Create a maintainable component library that follows shadcn/ui and Tailwind CSS patterns
* Enable faster development of new pages by providing ready-to-use components
* Establish clear component usage guidelines and documentation
* Implement custom React hooks to reduce duplicated data fetching and state management logic
* Design components for incremental adoption without breaking existing pages

## Non-goals (Strict)

* Redesigning the overall UI/UX or creating a new design system (use existing shadcn/ui patterns)
* Migrating existing pages to use new components (this is a separate phase/effort)
* Implementing advanced DataTable features like server-side pagination or virtual scrolling in the initial version
* Creating a full Storybook setup or comprehensive component playground
* Refactoring backend API contracts or data structures
* Implementing new business logic or features beyond component extraction
* Converting Server Components to Client Components or vice versa beyond what is necessary for component extraction
* Performance optimization beyond what naturally comes from reducing duplication

## Scope

### In scope

* Create shared components in vulcanlab_ui/src/components/:
  * PageLoadingState - Standardized loading displays
  * PageErrorState - Standardized error displays with retry functionality
  * StatsCard and StatsCardGrid - Metric display cards
  * DataTable - Generic table with configurable columns, sorting, and actions
  * StatusBadge - Universal status indicator with configurable color schemes
  * EmptyState - Standardized empty state displays
  * PageHeader - Consistent page headers with title, description, and actions
  * StickyDetailHeader - Detail page headers with back navigation
  * FormField - Form field wrapper with label, error display, and validation
  * ConfirmDialog - Generic confirmation dialog (generalize existing ConfirmDeleteModal)
* Create custom React hooks in vulcanlab_ui/src/hooks/:
  * usePageData - Data fetching with loading/error states
  * useTable - Table state management (sorting, selection)
  * useModal - Modal open/close state management
* Integrate react-hook-form for form validation following shadcn/ui patterns
* Add component usage guidelines to documentation/patterns.md
* Create markdown documentation files with usage examples for each new component
* Write unit tests for all new shared components using Jest and React Testing Library
* Ensure all components follow TypeScript strict mode and have proper type definitions
* Design components to be backward compatible allowing gradual migration

### Out of scope

* Migrating existing pages to use the new components (separate implementation phase)
* Implementing complex DataTable features like virtual scrolling, column resizing, or drag-and-drop
* Creating a component playground or Storybook setup
* Refactoring the backend API or data models
* Changing existing page functionality or business logic
* Implementing new features beyond component extraction
* Performance profiling and optimization
* Accessibility auditing (though components should follow basic a11y patterns from shadcn/ui)
* Internationalization (i18n) support
* Creating custom themes or variant systems beyond shadcn/ui defaults

## Requirements (Functional)

* R1: PageLoadingState component must accept title and description props and display a centered loading spinner consistent with existing loading patterns
* R2: PageErrorState component must accept error message, title, description, and optional retry callback, displaying error with retry button when provided
* R3: DataTable component must support configurable columns with type-safe TypeScript definitions, optional row click handlers, and action buttons
* R4: DataTable must support optional sorting functionality that can be enabled per-column via configuration
* R5: StatusBadge component must accept status string and configurable status-to-style mappings, rendering appropriate colors and icons
* R6: EmptyState component must accept icon, title, description, and optional action button props
* R7: StatsCard component must display metric label, value, optional icon, and optional trend indicator
* R8: StatsCardGrid component must accept array of stats and render them in responsive grid layout (3 columns on desktop, 1-2 on mobile)
* R9: PageHeader component must support title, description, and optional action buttons with flexible layout
* R10: StickyDetailHeader component must include back button navigation, title, subtitle, and optional action buttons with sticky positioning
* R11: FormField component must integrate with react-hook-form for validation and error display
* R12: ConfirmDialog component must support custom title, message, confirm/cancel button text, and variant (danger/warning/info)
* R13: usePageData hook must handle fetch lifecycle (loading, error, success states) and expose retry functionality
* R14: useTable hook must manage table state including sorting direction, selected rows (optional), and provide helper functions
* R15: useModal hook must manage modal open/close state and provide typed helper functions
* R16: All components must support className prop for custom styling via Tailwind utilities
* R17: All components must be exported from index files for easy importing
* R18: All components must have TypeScript prop type definitions with JSDoc comments
* R19: Components must follow existing shadcn/ui patterns and use existing UI primitives (Button, Card, Dialog, etc.)
* R20: Components must support both light and dark themes via next-themes without custom styling

## Requirements (Non-functional)

* Performance:
  * Components must not introduce performance regressions compared to inline implementations
  * DataTable must handle up to 100 rows efficiently without virtualization
  * Component re-renders must be minimized using React.memo where appropriate

* Reliability:
  * All components must have unit test coverage with at least happy path and error case tests
  * Components must handle edge cases gracefully (null/undefined props, empty arrays, missing data)
  * TypeScript strict mode must be enabled with no any types without justification

* Security / Privacy:
  * Components must not log sensitive data to console
  * Error messages displayed in PageErrorState must not expose internal system details
  * Form validation must happen on both client and server (client-side only for UX, server validates)

* Observability:
  * Components should use console.error for error logging in development
  * Component props should be well-typed to catch issues at compile time
  * Test coverage reports must be generated for all new components

## Proposed Solution (High-level)

* Create a new shared component library in vulcanlab_ui/src/components/ organized by component type
* Extract common UI patterns identified in the analysis into standalone, reusable components
* Use shadcn/ui primitives (Button, Card, Dialog, Table) as building blocks for higher-level components
* Implement composition pattern where complex components (like DataTable) compose simpler components
* Create custom hooks in vulcanlab_ui/src/hooks/ for common patterns (data fetching, table state, modals)
* Integrate react-hook-form for form handling following shadcn/ui form patterns
* Design components with sensible defaults but allow customization through props
* Use TypeScript generics where appropriate (e.g., DataTable<TData>, usePageData<TResponse>)
* Follow existing patterns from shadcn/ui for prop naming, styling, and composition
* Create markdown documentation files alongside component source files
* Update documentation/patterns.md with component usage guidelines and examples

**Main components and responsibilities:**

1. **Layout Components** (PageLoadingState, PageErrorState, EmptyState, PageHeader, StickyDetailHeader)
   * Provide consistent page structure and common states
   * Reduce duplication of layout patterns across pages

2. **Data Display Components** (DataTable, StatusBadge, StatsCard, StatsCardGrid)
   * Standardize data visualization patterns
   * Provide configurable, type-safe data display

3. **Form Components** (FormField with react-hook-form integration)
   * Standardize form field patterns with validation
   * Integrate with react-hook-form for consistent form handling

4. **Modal Components** (ConfirmDialog)
   * Provide reusable dialog patterns
   * Simplify common confirmation workflows

5. **Custom Hooks** (usePageData, useTable, useModal)
   * Extract common state management patterns
   * Reduce boilerplate in page components

**Data flow:**
1. Page component imports shared component from vulcanlab_ui/src/components/
2. Page passes props (data, callbacks, configuration) to shared component
3. Shared component renders UI using shadcn/ui primitives and Tailwind CSS
4. User interactions trigger callbacks passed from page component
5. Custom hooks manage common state patterns (loading, error, table state)

## Interfaces / APIs / Contracts

### Component Interfaces

**PageLoadingState**
```typescript
interface PageLoadingStateProps {
  title?: string;
  description?: string;
  className?: string;
}
```

**PageErrorState**
```typescript
interface PageErrorStateProps {
  error: string;
  title?: string;
  description?: string;
  onRetry?: () => void;
  className?: string;
}
```

**DataTable<TData>**
```typescript
interface DataTableColumn<TData> {
  key: string;
  header: string;
  cell: (row: TData) => React.ReactNode;
  sortable?: boolean;
  className?: string;
}

interface DataTableProps<TData> {
  data: TData[];
  columns: DataTableColumn<TData>[];
  onRowClick?: (row: TData) => void;
  loading?: boolean;
  emptyState?: React.ReactNode;
  className?: string;
}
```

**StatusBadge**
```typescript
interface StatusConfig {
  label: string;
  variant: 'default' | 'success' | 'warning' | 'error' | 'info';
  icon?: React.ComponentType<{ className?: string }>;
}

interface StatusBadgeProps {
  status: string;
  statusConfig: Record<string, StatusConfig>;
  className?: string;
}
```

**EmptyState**
```typescript
interface EmptyStateProps {
  icon?: React.ComponentType<{ className?: string }>;
  title: string;
  description?: string;
  action?: {
    label: string;
    onClick: () => void;
  };
  className?: string;
}
```

**StatsCard**
```typescript
interface StatsCardProps {
  label: string;
  value: string | number;
  icon?: React.ComponentType<{ className?: string }>;
  trend?: {
    value: number;
    direction: 'up' | 'down';
  };
  className?: string;
}
```

**PageHeader**
```typescript
interface PageHeaderProps {
  title: string;
  description?: string;
  actions?: React.ReactNode;
  className?: string;
}
```

**StickyDetailHeader**
```typescript
interface StickyDetailHeaderProps {
  title: string;
  subtitle?: string;
  backUrl: string;
  backLabel?: string;
  actions?: React.ReactNode;
  className?: string;
}
```

**FormField** (integrates with react-hook-form)
```typescript
interface FormFieldProps {
  label: string;
  error?: string;
  required?: boolean;
  description?: string;
  children: React.ReactNode;
  className?: string;
}
```

**ConfirmDialog**
```typescript
interface ConfirmDialogProps {
  open: boolean;
  onOpenChange: (open: boolean) => void;
  title: string;
  message: string;
  confirmLabel?: string;
  cancelLabel?: string;
  variant?: 'danger' | 'warning' | 'info';
  onConfirm: () => void | Promise<void>;
}
```

### Hook Interfaces

**usePageData<TData>**
```typescript
interface UsePageDataOptions {
  autoFetch?: boolean;
  onError?: (error: Error) => void;
}

interface UsePageDataReturn<TData> {
  data: TData | null;
  loading: boolean;
  error: string | null;
  refetch: () => Promise<void>;
}

function usePageData<TData>(
  fetchFn: () => Promise<TData>,
  options?: UsePageDataOptions
): UsePageDataReturn<TData>
```

**useTable<TData>**
```typescript
interface UseTableOptions<TData> {
  data: TData[];
  defaultSortKey?: string;
  defaultSortDirection?: 'asc' | 'desc';
}

interface UseTableReturn<TData> {
  sortedData: TData[];
  sortKey: string | null;
  sortDirection: 'asc' | 'desc';
  handleSort: (key: string) => void;
}

function useTable<TData>(options: UseTableOptions<TData>): UseTableReturn<TData>
```

**useModal**
```typescript
interface UseModalReturn {
  isOpen: boolean;
  open: () => void;
  close: () => void;
  toggle: () => void;
}

function useModal(defaultOpen?: boolean): UseModalReturn
```

## Data Model / Storage

Not applicable - this spec focuses on UI component extraction and does not introduce new data models or storage requirements. Components consume existing API response data structures.

## UX / Workflows

### Developer Workflow: Using Shared Components

1. Developer creates new page component
2. Import required shared components from @/components/
3. Use usePageData hook for data fetching with automatic loading/error handling
4. Render PageLoadingState and PageErrorState based on hook state
5. Pass data to DataTable or other display components with typed props
6. Use FormField with react-hook-form for forms with validation
7. Component handles rendering, state, and user interactions consistently

### Developer Workflow: Component Documentation

1. Developer needs to use a shared component
2. Reference component usage examples in markdown docs
3. Check TypeScript prop types for available configuration options
4. Import component and pass required props
5. Customize via className or optional props as needed

### User Experience Impact

* More consistent loading states across all pages (single spinner pattern)
* Consistent error messages with clear retry actions
* Uniform table styling and interaction patterns
* Consistent form validation feedback
* Predictable modal and dialog behaviors

## Testing Plan

* Unit tests:
  * Test each component renders correctly with required props
  * Test each component handles optional props correctly
  * Test each component renders empty/null/undefined states gracefully
  * Test interactive components (DataTable, ConfirmDialog) handle user interactions
  * Test FormField integrates correctly with react-hook-form
  * Test StatusBadge renders correct variant based on status config
  * Test custom hooks (usePageData, useTable, useModal) state transitions
  * Test usePageData handles fetch success, error, and retry scenarios
  * Test useTable handles sorting correctly in both directions
  * Test components accept and apply className prop correctly
  * Snapshot tests for component rendering (optional, for regression detection)

* Integration tests:
  * Not required for this phase - components are tested in isolation
  * Integration testing will occur when pages migrate to use components

* Manual test plan:
  * Verify components render correctly in both light and dark themes
  * Verify components are responsive across mobile, tablet, desktop viewports
  * Verify DataTable handles large datasets (50-100 rows) without performance issues
  * Verify FormField shows validation errors at appropriate times
  * Verify ConfirmDialog variants (danger/warning/info) display with correct styling
  * Verify StatusBadge renders with correct colors and icons for different statuses
  * Verify EmptyState displays correctly with and without action button
  * Verify StickyDetailHeader remains sticky during scroll
  * Verify all interactive elements are keyboard accessible (tab navigation)

## Acceptance Criteria (Checklist)

* [ ] All 10+ shared components implemented in vulcanlab_ui/src/components/
* [ ] All 3 custom hooks implemented in vulcanlab_ui/src/hooks/
* [ ] react-hook-form integrated and FormField component created
* [ ] TypeScript prop interfaces defined for all components with JSDoc comments
* [ ] All components support className prop for custom styling
* [ ] All components use existing shadcn/ui primitives (Button, Card, Dialog, etc.)
* [ ] Components follow shadcn/ui naming and composition patterns
* [ ] Unit tests written for all components with at least 80% coverage
* [ ] Unit tests written for all custom hooks
* [ ] Markdown documentation created for each component with usage examples
* [ ] Component usage guidelines added to documentation/patterns.md
* [ ] All components support light and dark themes without custom theme code
* [ ] Components handle edge cases (null/undefined props, empty data) gracefully
* [ ] DataTable supports configurable columns with TypeScript generics
* [ ] DataTable supports optional sorting functionality
* [ ] StatusBadge accepts configurable status mappings
* [ ] usePageData hook handles loading, error, and success states with retry
* [ ] useTable hook manages sorting state correctly
* [ ] Components are backward compatible (existing pages not broken)
* [ ] All code passes TypeScript strict mode compilation with no errors
* [ ] Components tested manually in light and dark modes
* [ ] Components tested manually across mobile, tablet, desktop viewports

## Rollout / Migration Plan

This spec covers Phase 1: Component Creation. Migration is out of scope but outlined here for context:

**Phase 1: Component Library Creation (This Spec)**
* Create all shared components and hooks
* Write tests and documentation
* No changes to existing pages

**Phase 2: Incremental Migration (Future Work)**
* Migrate pages one at a time or by feature area
* Start with high-traffic pages (corpus, RAG, simple-conversion)
* Test each migrated page thoroughly before moving to next
* Monitor for regressions after each migration
* Each migration should be a separate PR for easy review and rollback

**Rollback Strategy:**
* New components are additive and don't modify existing code
* If issues are found, new components can be removed without affecting existing pages
* Once migration begins, individual pages can be rolled back by reverting their migration PR

## Risks and Alternatives

* Risks:
  * Components may not cover all edge cases from existing implementations - mitigate by thorough testing and iterative refinement
  * React-hook-form integration may not fit all existing form patterns - mitigate by keeping FormField flexible and supporting multiple validation approaches
  * DataTable may grow complex over time - mitigate by keeping initial version simple with opt-in features
  * Developers may continue creating inline components instead of using shared library - mitigate with clear documentation and code review process
  * Components may become too opinionated and limit flexibility - mitigate by providing escape hatches via className and composition
  * Test maintenance burden for 10+ new components - mitigate by keeping tests focused and using test utilities

* Alternatives considered:
  * **Alternative 1:** Use a full component library like Mantine or Ant Design
    * Pros: Battle-tested components, comprehensive features
    * Cons: Large bundle size, different design patterns than current shadcn/ui setup, migration cost
    * Decision: Rejected - prefer building on existing shadcn/ui foundation
  * **Alternative 2:** Migrate to Server Components for all pages
    * Pros: Better performance, reduced client-side JavaScript
    * Cons: Large refactor, breaks existing client-side state patterns, out of scope
    * Decision: Rejected - keep existing architecture, focus on component extraction
  * **Alternative 3:** Create components and migrate pages simultaneously
    * Pros: Faster to see benefits, validates components immediately
    * Cons: Higher risk, larger PRs, harder to review and rollback
    * Decision: Rejected - prefer phased approach for lower risk
  * **Alternative 4:** Use a form library other than react-hook-form (Formik, React Final Form)
    * Pros: Different features and patterns
    * Cons: react-hook-form is most commonly used with shadcn/ui, better TypeScript support
    * Decision: Rejected - react-hook-form is the best fit for shadcn/ui patterns
  * **Alternative 5:** Build DataTable with full features (sorting, filtering, pagination, etc.) initially
    * Pros: Complete solution from the start
    * Cons: Over-engineering, longer implementation time, harder to maintain
    * Decision: Rejected - start simple with opt-in features, iterate based on actual needs

## Patterns and Standards Alignment (from documentation/patterns.md)

* Patterns applied:
  * **Frontend Stack** - Using Next.js, TypeScript, TailwindCSS v4, and Radix UI as specified
  * **Component Organization** - Creating components in vulcanlab_ui/src/components/ and vulcanlab_ui/src/components/ui/ as specified
  * **Styling** - Using TailwindCSS utility classes, avoiding CSS Modules
  * **TypeScript Conventions** - Using PascalCase for components, camelCase for variables/functions
  * **File Naming** - Using kebab-case for component files (data-table.tsx, page-loading-state.tsx)
  * **Composition** - Building on existing shadcn/ui primitives rather than creating custom implementations

* Deviations (if any):
  * **Client Components** - All new components will use "use client" directive because they involve interactivity (forms, buttons, state)
    * Reason: Components like DataTable, FormField, and ConfirmDialog require client-side interactivity
    * Closest compliant option: Keep components as Client Components but design them to be compatible with Server Component pages (accept data as props, no implicit data fetching in components themselves)
  * **react-hook-form dependency** - Adding new dependency not currently in project
    * Reason: react-hook-form is the most common and best-supported form library for shadcn/ui patterns
    * Closest compliant option: Keep forms lightweight with basic validation only, avoid complex validation schemas

## Implementation Notes (Non-binding)

* Consider using React.memo for components that receive large data arrays (DataTable) to prevent unnecessary re-renders
* DataTable column definitions could use a builder pattern in the future for more complex scenarios
* usePageData hook could be extended to support polling or real-time updates in the future
* StatusBadge could accept a global status config via context in the future to avoid passing config on every use
* Component file structure suggestion:
  * vulcanlab_ui/src/components/data-table.tsx - Component implementation
  * vulcanlab_ui/src/components/data-table.test.tsx - Unit tests
  * vulcanlab_ui/src/components/data-table.md - Documentation
* Consider creating an index.ts that exports all shared components for easier imports
* EmptyState could support custom illustrations or animations in the future
* FormField could be extended to support more input types (select, checkbox, radio) with specialized variants
* The existing ConfirmDeleteModal should be deprecated in favor of ConfirmDialog after testing
* Consider adding a Skeleton component for more sophisticated loading states in the future
* React Hook Form documentation for shadcn/ui integration: https://ui.shadcn.com/docs/components/form
* Testing library for components: @testing-library/react with @testing-library/jest-dom
* Consider using MSW (Mock Service Worker) for testing hooks that make API calls in the future

## Open Questions

* Q1: Should DataTable support multi-select with checkboxes in the initial version, or defer to future iteration?
* Q2: Should usePageData hook cache responses, or should each fetch be fresh?
* Q3: Should StatusBadge include built-in status configs for common statuses (completed, pending, failed, etc.) or require all configs to be passed as props?
* Q4: Should components be exported from a single index file or imported directly from individual component files?
* Q5: Should we create a separate documentation site (like a minimal Docusaurus setup) or stick with markdown files in the repo?
* Q6: Should FormField support field arrays (dynamic lists of inputs) in the initial version?
* Q7: Should we create a dedicated hook for form submission (useFormSubmit) or rely on react-hook-form's handleSubmit?
* Q8: Should PageHeader support breadcrumbs in the initial version?
