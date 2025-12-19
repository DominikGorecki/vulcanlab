# Ticket: ui-component-standardization.T03 - Page Header Components

## Source

* Spec: documentation/work/ui-component-standardization.spec.md
* Patterns: documentation/patterns.md

## Goal

* Create two page header components (PageHeader, StickyDetailHeader) for consistent page structure
* Enable standardized headers across all pages with flexible action slots
* Provide navigation patterns for detail pages

## Scope

### In scope

* Implement PageHeader component with title, description, and action buttons
* Implement StickyDetailHeader component with back navigation and sticky positioning
* Both components support className prop
* TypeScript prop interfaces with JSDoc comments
* Unit tests for both components
* Markdown documentation for both components

### Out of scope

* Breadcrumb navigation in PageHeader
* Animation on scroll for StickyDetailHeader
* Mobile-specific navigation patterns
* Integration with actual pages

## Dependencies

* Depends on: none (uses existing shadcn/ui primitives)
* Unblocks: Page implementations in future migration work

## Implementation plan

* Create PageHeader component:
  * Create vulcanlab_ui/src/components/page-header.tsx
  * Add "use client" directive
  * Define PageHeaderProps interface (title required, description, actions, className optional)
  * Render flex container with title as h1
  * Display optional description as paragraph
  * Render optional actions ReactNode in flex end position
  * Use TailwindCSS for responsive layout (stack on mobile, row on desktop)
  * Apply className to container
  * Add JSDoc comments with usage example
* Create StickyDetailHeader component:
  * Create vulcanlab_ui/src/components/sticky-detail-header.tsx
  * Add "use client" directive
  * Define StickyDetailHeaderProps interface (title, backUrl required, subtitle, backLabel, actions, className optional)
  * Use Next.js Link component for back navigation
  * Render sticky positioned header with back button (ArrowLeft icon from lucide-react)
  * Display title as h1 and optional subtitle
  * Render optional actions ReactNode
  * Apply sticky positioning with appropriate z-index and background
  * Apply className to container
  * Add JSDoc comments
* Write component documentation:
  * Create page-header.md with usage examples showing title-only and with actions
  * Create sticky-detail-header.md with usage example showing back navigation
* Write unit tests:
  * Test PageHeader renders title correctly
  * Test PageHeader renders description when provided
  * Test PageHeader renders actions ReactNode when provided
  * Test PageHeader applies className
  * Test StickyDetailHeader renders title and back button
  * Test StickyDetailHeader renders subtitle when provided
  * Test StickyDetailHeader renders actions when provided
  * Test StickyDetailHeader applies className
  * Test StickyDetailHeader back button has correct href
* Patterns to apply:
  * Frontend Stack - Next.js, TypeScript, TailwindCSS
  * Component Organization - Components in vulcanlab_ui/src/components/
  * Styling - TailwindCSS utility classes, sticky positioning
  * File Naming - kebab-case for component files
  * Client Components - Use "use client" for Link component interactivity
* Deviations (if any):
  * None - fully compliant with patterns.md

## Unit tests (required)

* Add tests for:
  * PageHeader: renders title, renders description when provided, does not render description when undefined, renders actions ReactNode, applies className, responsive layout classes present
  * StickyDetailHeader: renders title, renders back button with correct href, renders backLabel or default "Back", renders subtitle when provided, renders actions when provided, applies className, has sticky positioning classes, has appropriate z-index
* Suggested locations:
  * vulcanlab_ui/src/components/page-header.test.tsx
  * vulcanlab_ui/src/components/sticky-detail-header.test.tsx
* Mocking/fakes needed:
  * Mock Next.js Link component for testing navigation
  * Mock action buttons as simple ReactNode elements

## Acceptance criteria (checklist)

* [ ] PageHeader component implemented with TypeScript types and JSDoc
* [ ] StickyDetailHeader component implemented with TypeScript types and JSDoc
* [ ] Both components support className prop
* [ ] StickyDetailHeader uses Next.js Link for navigation
* [ ] StickyDetailHeader has sticky positioning with proper z-index
* [ ] Both components have "use client" directive
* [ ] Markdown documentation created for both components
* [ ] Unit tests written with at least 80% coverage
* [ ] All tests pass
* [ ] TypeScript compilation passes with strict mode
* [ ] Components tested manually in both light and dark themes

## Manual verification

* Steps:
  * Create test page with PageHeader showing title only
  * Create test page with PageHeader showing title, description, and action buttons
  * Create test detail page with StickyDetailHeader
  * Scroll the detail page to verify header remains sticky
  * Click back button to verify navigation works
  * Test on mobile, tablet, and desktop viewports
  * Toggle between light and dark themes
* Expected results:
  * PageHeader displays title and optional content with proper spacing
  * PageHeader actions align to the right on desktop, stack on mobile
  * StickyDetailHeader remains at top during scroll
  * Back button navigates to correct URL
  * Headers render correctly in both light and dark themes
  * Headers are responsive and readable on all viewport sizes

## Notes

* Requirements covered: R9, R10, R16, R17, R18, R19, R20
* PageHeader will be used on list/index pages (corpus, RAG, simple-conversion, etc.)
* StickyDetailHeader will be used on detail pages (work details, chunk details, etc.)
* Consider adding breadcrumb support to PageHeader in future iteration if needed
* z-index should be high enough to stay above content but not conflict with modals
* Back navigation should work with browser back button as well as the back link
* Test with long titles to ensure proper text wrapping
