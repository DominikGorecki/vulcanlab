# Ticket: work-summarization.T15 - UI: Summary Viewer Page

## Source

* Spec: documentation/work/work-summarization.spec.md
* Patterns: documentation/patterns.md

## Goal

* Create summary viewer page displaying combined summary for a work
* Show headings with their LLM-generated summaries in document order
* Provide navigation back to summaries list

## Phase

* Frontend

## Scope

### In scope

* New page `vulcanlab_ui/src/app/summaries/[work_id]/page.tsx`
* Fetch and display summary sections ordered by start_line
* Render heading titles and summary content as markdown
* Navigation header with back link

### Out of scope

* Summary editing (not in spec)
* Re-summarization from this page (use workflow page)
* Export functionality (not in scope)

## Dependencies

* Depends on: T11 (get summary API endpoint), T14 (navigation from list)
* Unblocks: T16

## Implementation plan

1. Create `vulcanlab_ui/src/app/summaries/[work_id]/page.tsx`
2. Implement data fetching:
   - Extract `work_id` from params
   - Use `usePageData` with `useCallback`
   - Fetch from `GET /api/v1/summarize/works/{work_id}/summary`
3. Implement header:
   - Use `StickyDetailHeader` component
   - Title: "Summary"
   - Subtitle: work_title from response
   - Back link to `/summaries`
4. Render summary sections:
   - Map over `sections` array (already ordered by start_line)
   - For each section:
     - Display heading as H2/H3 based on original level (or just H2 for simplicity)
     - Display summary_content rendered as markdown
     - Optionally show line reference (start_line) as subtle metadata
5. Use markdown rendering:
   - Use existing markdown component or react-markdown
   - Support standard markdown: headings, lists, bold, italic, code
6. Add styling:
   - Section spacing
   - Visual separation between sections
   - Consistent typography with rest of app
7. Handle empty/partial states:
   - Loading state while fetching
   - Error state if work not found
   - Message if summary has zero sections
8. Add action buttons (optional):
   - "Re-summarize" button linking to `/summaries/workflow/{work_id}`
   - "View Original" button linking to `/corpus/{work_id}`

* Patterns to apply:
  * **Page Lifecycle Pattern** - usePageData for fetching
  * **StickyDetailHeader** - Standard detail page header
  * **useCallback** - Wrap fetch function
* Deviations (if any):
  * None

## Unit tests (required)

* Add tests for:
  * Page renders loading state initially
  * Page fetches correct work_id from params
  * Sections render in order
  * Heading titles display correctly
  * Summary content renders as markdown
  * Back navigation link works
  * Error state shown for invalid work_id
  * Empty state shown if no sections
* Suggested locations:
  * `vulcanlab_ui/src/app/summaries/[work_id]/__tests__/page.test.tsx`
* Mocking/fakes needed:
  * Mock fetch for API response
  * Mock useParams for work_id
  * Mock StickyDetailHeader component

## Acceptance criteria (checklist)

* [ ] Page renders at `/summaries/{work_id}`
* [ ] Work title displayed in header
* [ ] Back link navigates to `/summaries`
* [ ] Summary sections displayed in document order
* [ ] Heading titles visible for each section
* [ ] Summary content rendered as markdown
* [ ] Loading and error states work correctly
* [ ] Unit tests pass

## Manual verification

* Steps:
  * Complete summarization workflow for a work (T13)
  * Navigate to `/summaries`
  * Click on the summarized work
  * Verify summary viewer displays
  * Check heading titles match original document structure
  * Check summary content is readable and formatted
  * Click back link to return to list
* Expected results:
  * Full summary displayed with clear structure
  * Markdown rendering works (lists, bold, etc.)
  * Navigation smooth

## Notes

* Requirements covered: R12 (display combined summary ordered by start_line)
* Summary should feel like reading an executive summary of the document
* Consider adding a "Table of Contents" sidebar for long summaries (future enhancement)
* Markdown renderer should handle code blocks, tables if LLM outputs them
