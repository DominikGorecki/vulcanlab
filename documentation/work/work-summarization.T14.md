# Ticket: work-summarization.T14 - Summarize List Page and Navigation

## Source

* Spec: documentation/work/work-summarization.spec.md
* Patterns: documentation/patterns.md

## Goal

* Add "Summarize" item to left navigation bar
* Create Summarize list page showing works with summaries
* Display summary status and available derived outputs per work

## Phase

* Frontend

## Scope

### In scope

* Add nav item to vulcanlab_ui/src/components/nav-bar.tsx
* Create vulcanlab_ui/src/app/summarize/page.tsx list page
* DataTable displaying works with summaries
* Columns: work title, node count, available summary types, actions
* Click row to navigate to work summary detail
* Empty state when no works have summaries
* Loading and error states

### Out of scope

* Work summary detail page (T15)
* Corpus page Summarize button (T16)
* Derived output generation (T15)

## Dependencies

* Depends on: T11 (GET /api/v1/summarize/works endpoint)
* Unblocks: T15

## Implementation plan

1. Update vulcanlab_ui/src/components/nav-bar.tsx:
   - Import BookOpen icon from lucide-react
   - Add nav item: { href: "/summarize", label: "Summarize", icon: BookOpen, alwaysVisible: true }
   - Position after "Collections" or "Corpus" in nav order
2. Create vulcanlab_ui/src/app/summarize/page.tsx:
   - "use client" directive
   - Define SummarizedWork interface matching API response
3. Implement data fetching:
   - useCallback-wrapped fetch function for GET /api/v1/summarize/works
   - usePageData hook for loading/error/data states
4. Define table columns:
   - Title: work title, clickable link to /summarize/[id]
   - Nodes: node_count number
   - Summaries: badges showing available types (Abstract, Outline, etc.)
   - Actions: "View" button
5. Implement page layout:
   - PageHeader with title "Summarize" and subtitle
   - DataTable with columns
   - EmptyState when no works: "No works have been summarized yet. Go to Corpus to summarize a work."
6. Handle loading state with PageLoadingState
7. Handle error state with PageErrorState with retry
8. Add click handler to navigate to /summarize/[work_id]
* Patterns to apply:
  * Page Lifecycle Pattern with usePageData
  * useCallback for fetch function
  * DataTable for tabular data
  * PageHeader for page title
  * EmptyState for no data
  * StatusBadge for summary type indicators
* Deviations (if any):
  * None

## Unit tests (required)

* Add tests for:
  * Nav bar includes Summarize item with correct href
  * Page renders loading state initially
  * Page displays table after data loads
  * Table shows correct columns
  * Empty state shown when no summarized works
  * Row click navigates to detail page
  * Summary type badges display correctly
  * Error state shown on fetch failure
  * Retry button triggers refetch
* Suggested locations:
  * vulcanlab_ui/src/components/__tests__/nav-bar.test.tsx (update existing)
  * vulcanlab_ui/src/app/summarize/__tests__/page.test.tsx
* Mocking/fakes needed:
  * Mock fetch for API calls
  * Mock useRouter for navigation

## Acceptance criteria (checklist)

* [ ] "Summarize" appears in left navigation
* [ ] Summarize page accessible at /summarize
* [ ] Table displays works with summaries
* [ ] Node count shown for each work
* [ ] Available summary types shown as badges
* [ ] Empty state when no summarized works
* [ ] Loading state during fetch
* [ ] Error state with retry on failure
* [ ] Row click navigates to detail page
* [ ] All unit tests pass

## Manual verification

* Steps:
  1. Start frontend dev server
  2. Verify "Summarize" appears in left nav
  3. Click to navigate to /summarize
  4. If no summarized works, verify empty state
  5. After summarizing a work, refresh and verify it appears
  6. Click work row to navigate to detail
* Expected results:
  * Navigation works correctly
  * List displays summarized works
  * Detail navigation functions

## Notes

* Requirements covered: R13
* Icon choice: BookOpen represents summary/digest concept
* Badge colors for summary types: consider using consistent palette
* Consider adding "Summarize a work" action button in empty state linking to Corpus
* Data refresh could be manual (refresh button) or automatic (polling) - start with manual
