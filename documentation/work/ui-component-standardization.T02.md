# Ticket: ui-component-standardization.T02 - Layout State Components

## Source

* Spec: documentation/work/ui-component-standardization.spec.md
* Patterns: documentation/patterns.md

## Goal

* Create three foundational layout state components (PageLoadingState, PageErrorState, EmptyState)
* These components provide standardized UI for common page states
* Enable immediate visual testing and usage in any page

## Scope

### In scope

* Implement PageLoadingState component with centered spinner
* Implement PageErrorState component with error display and optional retry button
* Implement EmptyState component with icon, title, description, and optional action
* All components support className prop for custom styling
* All components use existing shadcn/ui primitives (Button, Card)
* TypeScript prop interfaces with JSDoc comments
* Unit tests for all components
* Markdown documentation for each component

### Out of scope

* Advanced loading states (skeleton loaders, progress bars)
* Animated transitions between states
* Integration with actual pages
* Custom illustrations for EmptyState

## Dependencies

* Depends on: none (uses existing shadcn/ui primitives)
* Unblocks: T06 (components can be used with usePageData hook)

## Implementation plan

* Create PageLoadingState component:
  * Create vulcanlab_ui/src/components/page-loading-state.tsx
  * Add "use client" directive
  * Define PageLoadingStateProps interface (title, description, className optional)
  * Render centered div with loading spinner (use lucide-react Loader2 icon)
  * Display optional title and description
  * Apply className to container for customization
  * Add JSDoc comments
* Create PageErrorState component:
  * Create vulcanlab_ui/src/components/page-error-state.tsx
  * Add "use client" directive
  * Define PageErrorStateProps interface (error required, title, description, onRetry, className optional)
  * Render centered div with error icon (AlertCircle from lucide-react)
  * Display error message, optional title and description
  * Conditionally render retry Button when onRetry callback is provided
  * Use existing Button component from vulcanlab_ui/src/components/ui/
  * Apply className to container
  * Add JSDoc comments
* Create EmptyState component:
  * Create vulcanlab_ui/src/components/empty-state.tsx
  * Add "use client" directive
  * Define EmptyStateProps interface (title required, icon, description, action, className optional)
  * Render centered div with optional icon component
  * Display title and optional description
  * Conditionally render action Button when action prop provided
  * Use existing Button component
  * Apply className to container
  * Add JSDoc comments
* Write component documentation:
  * Create page-loading-state.md with usage example
  * Create page-error-state.md with usage example
  * Create empty-state.md with usage example
* Write unit tests:
  * Test each component renders with required props
  * Test optional props are handled correctly
  * Test className is applied
  * Test PageErrorState shows retry button only when onRetry provided
  * Test EmptyState shows action button only when action provided
  * Test components handle null/undefined optional props gracefully
* Patterns to apply:
  * Frontend Stack - Next.js, TypeScript, TailwindCSS, Radix UI
  * Component Organization - Components in vulcanlab_ui/src/components/
  * Styling - TailwindCSS utility classes only
  * File Naming - kebab-case for component files
  * Client Components - Use "use client" directive for interactivity
* Deviations (if any):
  * None - fully compliant with patterns.md

## Unit tests (required)

* Add tests for:
  * PageLoadingState: renders with default spinner, renders with title, renders with description, applies className correctly
  * PageErrorState: renders error message, renders with title and description, shows retry button when onRetry provided, does not show retry button when onRetry is undefined, retry button calls onRetry when clicked, applies className
  * EmptyState: renders title, renders with icon component, renders with description, shows action button when action provided, does not show action button when action is undefined, action button calls onClick, applies className
* Suggested locations:
  * vulcanlab_ui/src/components/page-loading-state.test.tsx
  * vulcanlab_ui/src/components/page-error-state.test.tsx
  * vulcanlab_ui/src/components/empty-state.test.tsx
* Mocking/fakes needed:
  * Mock icon components (simple mock React components)
  * Mock Button component from ui/ if needed for isolation

## Acceptance criteria (checklist)

* [ ] PageLoadingState component implemented with TypeScript types and JSDoc
* [ ] PageErrorState component implemented with TypeScript types and JSDoc
* [ ] EmptyState component implemented with TypeScript types and JSDoc
* [ ] All components support className prop
* [ ] All components use existing shadcn/ui primitives (Button, icons from lucide-react)
* [ ] All components have "use client" directive
* [ ] Markdown documentation created for all components
* [ ] Unit tests written with at least 80% coverage
* [ ] All tests pass
* [ ] TypeScript compilation passes with strict mode
* [ ] Components tested in both light and dark themes manually

## Manual verification

* Steps:
  * Create a test page in vulcanlab_ui/src/app/test-components/page.tsx
  * Import and render PageLoadingState with and without title/description
  * Import and render PageErrorState with and without retry callback
  * Import and render EmptyState with and without icon/action
  * Toggle between light and dark themes
  * Verify centering, spacing, and visual consistency
  * Click retry button and action button to verify callbacks
* Expected results:
  * PageLoadingState shows centered spinner with optional text
  * PageErrorState shows error with red/warning styling and conditional retry button
  * EmptyState shows centered empty state with optional icon and action
  * All components render correctly in both light and dark themes
  * Buttons are clickable and trigger callbacks
  * Components are responsive on mobile and desktop viewports

## Notes

* Requirements covered: R1, R2, R6, R16, R17, R18, R19, R20
* These are the most fundamental components - they establish patterns for all other components
* PageLoadingState will be used with usePageData hook for consistent loading UI
* PageErrorState will be used with usePageData hook for consistent error UI
* EmptyState will be used in DataTable and other components when data is empty
* Consider using Card component for better visual containment if needed
* Test with actual error messages from API to verify they display correctly
