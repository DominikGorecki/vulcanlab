# Ticket: simplify-ui-with-simple-conversion-focus.T07 - Frontend: Conversion Detail Page

## Source
- Spec: documentation/work/simplify-ui-with-simple-conversion-focus.spec.md
- Patterns: documentation/patterns.md

## Goal
- Create detail page at /simple-conversion/history/[work_id] to view full conversion results
- Display summary card with metadata, counts (separated heading/content), status, mode
- Show scrollable list of all chunks matching post-conversion results view
- Include navigation: back button and "Start New Conversion" button
- Handle invalid work_id and failed conversion states

## Scope
### In scope
- New Next.js page at vulcanlab_ui/src/app/simple-conversion/history/[work_id]/page.tsx
- Fetch data from existing /api/simple-conversion/results/{work_id} endpoint
- Summary card component displaying: title, author, classification badge, mode badge, status, token count, chunk counts (total, heading, content), error message if failed
- Chunks list component showing: heading level badge, heading text, line range, content preview
- Back button navigating to /simple-conversion
- "Start New Conversion" button navigating to /simple-conversion with form reset intent
- Loading state while fetching data
- Error state for invalid work_id or fetch failure
- Not found state if work doesn't exist or isn't a simple conversion

### Out of scope
- Edit or delete functionality
- Re-run conversion action
- Export or download results
- Comparison with other conversions
- Inline chunk editing
- Filtering or searching chunks

## Dependencies
- Depends on: T05 (navigation from history list to detail page)
- Unblocks: none (completes history viewing feature)

## Implementation plan
1. Create directory vulcanlab_ui/src/app/simple-conversion/history/[work_id]/
2. Create page.tsx in that directory with default export
3. Add "use client" directive for data fetching and interactivity
4. Extract work_id from Next.js params
5. Add state for results data, loading, error
6. Create useEffect to fetch /api/simple-conversion/results/{work_id} on mount
7. Parse response to extract:
   - Work metadata (title, author, year, classification, token_count)
   - Processing status (mode, step, error)
   - Chunks array
8. Calculate heading vs content chunk counts from chunks array:
   - Heading: level in ['H1', 'H2', 'H3', 'H4', 'H5']
   - Content: level ends with '-chunk' or equals 'chunk'
9. Create SimpleConversionSummaryCard component:
   - Props: title, author, classification, mode, status, token_count, chunk_count, heading_chunk_count, content_chunk_count, error_message
   - Render Card with all metrics
   - Show error banner if error_message present
10. Create or reuse ChunkListItem component:
    - Props: level, heading, line_range, content
    - Render level badge (H1-H5 with hierarchy color, content chunks different color)
    - Show heading text and line range
    - Show content preview (truncated or expandable)
11. Render page structure:
    - Back button (arrow icon + "Back to Simple Conversion")
    - Summary card
    - Chunks section heading ("Chunks")
    - Scrollable chunks list
    - "Start New Conversion" button at bottom
12. Handle error states: 404 if work not found, 400 if not simple conversion, network errors
13. Handle loading state with skeleton UI matching final layout
14. Style with TailwindCSS: appropriate spacing, scrollable chunks container, responsive layout

- Patterns to apply:
  - **Next.js App Router** - Dynamic route with [work_id] param
  - **Client Components** - "use client" for fetching and interactivity
  - **TailwindCSS** - Utility classes for layout and styling
  - **Shadcn/Radix Components** - Reuse Card, Badge, Button from UI kit
  - **Component Composition** - Extract summary card and chunk item as reusable components

- Deviations (if any):
  - None - follows Next.js App Router patterns for dynamic routes

## Unit tests (required)
- Add tests for:
  - Page extracts work_id from params correctly
  - Page fetches /api/simple-conversion/results/{work_id} on mount
  - Loading state shown while fetching
  - Summary card renders with correct data when fetch succeeds
  - Chunks list renders all chunks from response
  - Heading chunk count calculated correctly from chunks array
  - Content chunk count calculated correctly from chunks array
  - Error banner shown when conversion failed (error_message present)
  - 404 state shown when work_id does not exist
  - Error state shown when fetch fails
  - Back button navigates to /simple-conversion
  - "Start New Conversion" button navigates to /simple-conversion
  - Mode badge shows correct value (automatic/manual)
  - Status indicator shows correct state (success/failed)
  - Classification badge shows correct value (small/large)
- Suggested locations:
  - vulcanlab_ui/src/app/simple-conversion/history/[work_id]/__tests__/page.test.tsx
  - vulcanlab_ui/src/components/simple-conversion/__tests__/SimpleConversionSummaryCard.test.tsx
- Mocking/fakes needed:
  - Mock fetch/API client for results endpoint
  - Mock useRouter and useParams from next/navigation
  - Mock response data with various scenarios (success, failed, different chunk types)

## Acceptance criteria (checklist)
- [ ] Page exists at /simple-conversion/history/[work_id]
- [ ] Page fetches conversion results from API on mount
- [ ] Loading state shown while fetching (skeleton UI)
- [ ] Summary card displays all required fields: title, author, classification, mode, status, token count, chunk counts
- [ ] Heading chunk count and content chunk count shown separately
- [ ] Total chunk count shown and matches heading + content counts
- [ ] Mode badge displays automatic or manual
- [ ] Status indicator shows success or failed
- [ ] Error banner shown at top if conversion failed
- [ ] Error message displayed in banner
- [ ] Chunks list shows all chunks with level badges, headings, line ranges
- [ ] Chunks list scrollable if many chunks present
- [ ] Back button navigates to /simple-conversion
- [ ] "Start New Conversion" button navigates to /simple-conversion
- [ ] 404 state shown for invalid work_id
- [ ] Error state shown for fetch failures
- [ ] Unit tests cover rendering, fetching, navigation, and error states

## Manual verification
- Steps:
  1. Navigate to /simple-conversion page
  2. Click on a past conversion in history list
  3. Verify navigation to /simple-conversion/history/[work_id]
  4. Verify summary card shows correct metadata and counts
  5. Check that heading_chunk_count + content_chunk_count = chunk_count
  6. Scroll chunks list and verify all chunks present
  7. Verify level badges differ for headings vs content chunks
  8. Click Back button and verify return to /simple-conversion
  9. Navigate to detail page again
  10. Click "Start New Conversion" button
  11. Verify navigation to /simple-conversion (form ready for new entry)
  12. Navigate to /simple-conversion/history/999999 (invalid ID)
  13. Verify 404 or error state shown
  14. Find failed conversion in history and click
  15. Verify error banner and message shown on detail page
- Expected results:
  - Detail page loads quickly and shows complete information
  - Chunk counts accurately reflect database state
  - Navigation buttons work correctly
  - Error states are user-friendly and actionable
  - Layout is responsive and readable
  - No console errors

## Notes
- Existing /api/simple-conversion/results/{work_id} endpoint returns full chunk details, no modification needed
- Chunk count calculation should match the backend history endpoint logic (T03) for consistency
- Consider using React Virtualization (react-window) if chunk lists are very long (100+ chunks)
- Level badge colors: establish clear visual hierarchy (H1 largest/darkest, content chunks neutral color)
- Content preview in chunks: truncate long content to ~200 chars with "..." or add expand/collapse
- Summary card layout: consider two-column layout on desktop for better space usage
- Back button: use router.back() or Link with href="/simple-conversion"
- "Start New Conversion" button: consider adding intent to clear form state if form is stateful
- Error banner styling: use existing alert/error component patterns for consistency
- Breadcrumb navigation could be added later: Home > Simple Conversion > [Title]
- Consider adding print-friendly CSS for users who want to print results
- Status badge should match colors used in history list (T05) for consistency
