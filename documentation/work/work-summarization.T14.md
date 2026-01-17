# Ticket: work-summarization.T14 - UI: Summaries List Page and Navigation

## Source

* Spec: documentation/work/work-summarization.spec.md
* Patterns: documentation/patterns.md

## Goal

* Create Summaries list page showing all works with summaries
* Add "Summaries" link to left navigation
* Enable navigation to summary viewer from list

## Phase

* Frontend

## Scope

### In scope

* New page `vulcanlab_ui/src/app/summaries/page.tsx`
* Add "Summaries" link to left navigation component
* DataTable displaying works with summaries
* Navigation to summary viewer on row click

### Out of scope

* Summary viewer page (T15)
* Workflow page (T13, already done)
* Settings tab (T16)

## Dependencies

* Depends on: T11 (list works API endpoint)
* Unblocks: T15

## Implementation plan

1. Create `vulcanlab_ui/src/app/summaries/page.tsx`
2. Implement data fetching:
   - Use `usePageData` with `useCallback`
   - Fetch from `GET /api/v1/summarize/works`
3. Define columns for DataTable:
   - ID (work_id)
   - Title
   - Summary Count (number of sections summarized)
   - Last Updated (formatted date)
4. Implement row click navigation:
   - Navigate to `/summaries/{work_id}` on click
5. Add empty state:
   - "No summaries yet" message
   - Link/button to go to Corpus page
6. Add page header:
   - Title: "Summaries"
   - Description: "View generated summaries for your works"
7. Update left navigation component:
   - Find navigation component (likely in `components/` or layout)
   - Add "Summaries" link with appropriate icon (e.g., `FileText`)
   - Position after Corpus or in logical location
8. Add loading and error states:
   - Use `PageLoadingState` and `PageErrorState`

* Patterns to apply:
  * **Page Lifecycle Pattern** - usePageData hook
  * **DataTable** - Standard table component
  * **useCallback** - Wrap fetch function
* Deviations (if any):
  * None

## Unit tests (required)

* Add tests for:
  * Page renders loading state initially
  * DataTable displays fetched works
  * Columns show correct data (id, title, count, date)
  * Row click navigates to correct summary URL
  * Empty state shown when no summaries
  * Error state shown on API failure
  * Navigation link appears in sidebar
* Suggested locations:
  * `vulcanlab_ui/src/app/summaries/__tests__/page.test.tsx`
* Mocking/fakes needed:
  * Mock fetch for API response
  * Mock useRouter for navigation
  * Mock PageLoadingState, PageErrorState, DataTable components

## Acceptance criteria (checklist)

* [ ] Summaries page renders at `/summaries`
* [ ] DataTable displays works with summaries
* [ ] Columns show work_id, title, summary_count, last_updated
* [ ] Clicking row navigates to `/summaries/{work_id}`
* [ ] Empty state displays when no summaries exist
* [ ] Loading and error states work correctly
* [ ] "Summaries" link appears in left navigation
* [ ] Unit tests pass

## Manual verification

* Steps:
  * Ensure at least one work has summaries (complete workflow from T13)
  * Navigate to `/summaries`
  * Verify table shows summarized works
  * Click on a work row
  * Verify navigation to summary viewer
  * Check left navigation for Summaries link
* Expected results:
  * Table displays correct data
  * Navigation works
  * Left nav includes Summaries link

## Notes

* Requirements covered: R12 (display combined summary - list portion)
* Left navigation component location may vary - search for existing nav implementation
* Date formatting should match existing patterns in codebase (e.g., corpus page)
* Consider adding "Start Summarizing" action button that goes to Corpus page
