# Ticket: corpus-search-feature.T05 - Document Viewer with Highlighting and Auto-Scroll

## Source

* Spec: documentation/work/corpus-search-feature.spec.md
* Patterns: documentation/patterns.md

## Goal

* Implement document viewer page for viewing full sanitized markdown with highlighted passages
* Add click-through navigation from search results to document viewer
* Implement passage highlighting by line numbers
* Auto-scroll to highlighted passage on page load
* Build reusable document viewer infrastructure at `/search/result/[chunk_id]/[start_line]/[end_line]`

## Scope

### In scope

* Backend API: Add `GET /api/v1/chunks/{chunk_id}/markdown` endpoint to fetch sanitized markdown
* Frontend: Create dynamic route `/search/result/[chunk_id]/[start_line]/[end_line]`
* Frontend: Document viewer component with markdown rendering
* Frontend: Passage highlighting based on line numbers
* Frontend: Auto-scroll to highlighted passage on load
* Frontend: Make search result cards clickable to navigate to viewer
* Unit tests for markdown fetching endpoint

### Out of scope

* Markdown editing or annotation
* Side-by-side comparison of chunks
* Export or print functionality
* Search within document
* Navigation between chunks (prev/next chunk)

## Dependencies

* Depends on: T01, T02, T03, T04
* Unblocks: none (final ticket)

## Implementation plan

1. Add `GET /api/v1/chunks/{chunk_id}/markdown` endpoint:
   - Create in `src/vulcanlab_api/routers/search.py` (or `chunks.py` if more appropriate)
   - Path parameter: chunk_id (int)
   - Query chunk from database to get work_id, start_line, end_line
   - Fetch work from database to get work_id, title
   - Load sanitized markdown from filesystem using work_id (check existing patterns for file path)
   - Return JSON: `{ work_id, work_title, markdown_content, chunk_start_line, chunk_end_line }`
   - Handle 404 if chunk or markdown file not found
   - Log request at INFO level
2. Create dynamic route `vulcanlab_ui/src/app/search/result/[chunk_id]/[start_line]/[end_line]/page.tsx`:
   - Extract params: chunk_id, start_line, end_line from URL
   - "use client" component
   - Fetch markdown via `GET /api/v1/chunks/{chunk_id}/markdown`
   - Use `usePageData` hook pattern with memoized fetch function
   - Display PageLoadingState, PageErrorState as needed
3. Implement markdown rendering and highlighting:
   - Install `react-markdown` if not already installed
   - Parse markdown_content into lines (split by newline)
   - Identify target lines: lines between start_line and end_line (inclusive)
   - Render markdown using `react-markdown` or similar
   - Apply custom renderer to wrap target lines in `<mark>` or `<span>` with highlight class
   - Alternative approach: split markdown into three sections (before, target, after) and render separately with different styling
   - Use CSS class with yellow background or border for highlighted lines
4. Implement auto-scroll to highlighted passage:
   - After rendering, find DOM element for highlighted passage (use ref or querySelector)
   - Call `element.scrollIntoView({ behavior: 'smooth', block: 'center' })` on page load
   - Use `useEffect` hook with empty dependency array to run once
5. Update search result cards to be clickable:
   - Wrap result card in `<Link>` or add onClick handler
   - Navigate to `/search/result/${chunk.chunk_id}/${chunk.start_line}/${chunk.end_line}`
   - Use Next.js router for navigation
6. Add "Back to Search" button in document viewer:
   - Use router.back() or Link to `/search`
   - Position at top of viewer page
7. Add unit tests for markdown endpoint:
   - Test valid chunk_id returns markdown with correct metadata
   - Test invalid chunk_id returns 404
   - Test chunk exists but markdown file missing returns 404 or error
   - Mock filesystem access for markdown file
8. Optional: Add tests for frontend highlighting logic:
   - Test line identification: lines 10-20 highlighted in 100-line document
   - Test edge cases: start_line=1, end_line=last line
   - Test single-line highlight (start_line=end_line)

* Patterns to apply:
  * Three-tier architecture - API endpoint in router, UI in dynamic route
  * API versioning - Use `/api/v1/chunks/{chunk_id}/markdown`
  * Page lifecycle pattern - Use usePageData hook
  * Component composition - Create reusable MarkdownViewer component
  * Theme awareness - Use Tailwind classes for highlight styling
  * Global exception handling - Raise HTTPException for 404s

* Deviations (if any):
  * None

## Unit tests (required)

* Add tests for:
  * Markdown endpoint returns correct work metadata (work_id, work_title)
  * Markdown endpoint returns markdown content as string
  * Markdown endpoint returns correct chunk line numbers (start_line, end_line)
  * Markdown endpoint returns 404 for non-existent chunk_id
  * Markdown endpoint returns 404 if sanitized markdown file not found
  * Markdown endpoint loads file from correct path (based on work_id)
  * Frontend: line identification logic correctly identifies target lines
  * Frontend: highlight class applied to target lines only
  * Frontend: auto-scroll scrolls to highlighted element

* Suggested locations:
  * `tests/unit/test_chunks_api.py` (for markdown endpoint)
  * `vulcanlab_ui/src/app/search/result/[chunk_id]/[start_line]/[end_line]/__tests__/page.test.tsx` (optional frontend tests)

* Mocking/fakes needed:
  * Mock database session with chunk and work data
  * Mock filesystem access to markdown file (return fixed markdown content)
  * Mock scrollIntoView method (in frontend tests)

## Acceptance criteria (checklist)

* [ ] Markdown endpoint `GET /api/v1/chunks/{chunk_id}/markdown` returns work metadata and content
* [ ] Markdown endpoint returns 404 for invalid chunk_id or missing file
* [ ] Document viewer page renders at `/search/result/[chunk_id]/[start_line]/[end_line]`
* [ ] Document viewer displays full sanitized markdown using react-markdown
* [ ] Document viewer highlights passage corresponding to start_line and end_line
* [ ] Highlighted passage has distinct visual styling (yellow background or border)
* [ ] Document viewer auto-scrolls to highlighted passage on page load
* [ ] Search result cards are clickable and navigate to document viewer
* [ ] Document viewer includes "Back to Search" button
* [ ] Document viewer displays work title at top
* [ ] Document viewer is theme-aware (dark/light mode)
* [ ] Unit tests pass for markdown endpoint
* [ ] Manual verification confirms highlighting and scrolling work correctly

## Manual verification

* Steps:
  1. Navigate to `/search` and perform a search
  2. Click on a search result card
  3. Verify browser navigates to `/search/result/[chunk_id]/[start_line]/[end_line]`
  4. Verify document viewer loads and displays full sanitized markdown
  5. Verify work title displays at top of page
  6. Verify passage corresponding to chunk's line range is highlighted (yellow background or border)
  7. Verify page auto-scrolls to bring highlighted passage into view
  8. Scroll up and down to view full document context
  9. Click "Back to Search" button -> verify returns to search results
  10. Test with chunk at beginning of document (start_line near 1)
  11. Test with chunk at end of document (end_line near last line)
  12. Test with single-line chunk (start_line = end_line)
  13. Toggle dark mode -> verify highlight styling remains visible
  14. Test with invalid chunk_id (e.g., 999999) -> verify 404 page displays

* Expected results:
  * Click on search result navigates to document viewer
  * Document viewer displays full markdown with formatted rendering
  * Target passage highlighted with distinct styling
  * Page auto-scrolls to bring highlight into center of viewport
  * "Back to Search" button returns to search results
  * Highlighting works at document edges (start, end)
  * Single-line highlights work correctly
  * Highlight visible in both light and dark mode
  * Invalid chunk_id shows 404 error page

## Notes

* Requirements covered: R10, R11, R12, R13
* Document viewer URL pattern `/search/result/[chunk_id]/[start_line]/[end_line]` is reusable for other features
* Sanitized markdown file path should match existing pattern (check work storage location)
* Line-based highlighting may be fragile if markdown is regenerated with different line breaks
* Alternative: use character offsets instead of line numbers (more complex but more robust)
* Markdown rendering should support syntax highlighting for code blocks
* Consider adding chunk metadata sidebar (breadcrumb, bibliographic info) in future iteration
* Auto-scroll should use smooth scrolling for better UX
* Highlight styling should be accessible (sufficient contrast in both themes)
* This ticket completes the search feature end-to-end workflow
