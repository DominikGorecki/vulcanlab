# Ticket: cleanup-chunks.T03 - Cleanup UI Page with Search and Results Display

## Source
- Spec: documentation/work/cleanup-chunks.spec.md
- Patterns: documentation/patterns.md

## Goal
- Create /cleanup page in Next.js with navigation link and search functionality
- Implement search form, paginated results display, and empty states
- Enable first vertical slice: users can search for chunks and see results end-to-end
- Follow Next.js App Router patterns with client components for interactivity

## Scope
### In scope
- Add "Cleanup" navigation link to nav-bar.tsx above Settings
- Create `/cleanup` route at `vulcanlab_ui/src/app/cleanup/page.tsx`
- Implement search form with text input and search button
- Display paginated search results showing chunk metadata
- Implement pagination controls (Previous/Next buttons, page indicator)
- Empty state for initial load and no results
- Use existing Shadcn/Radix UI components (Button, Card, Input, Badge)
- Client-side state management for search query and results
- Fetch from search API endpoint (GET /api/v1/chunks/search)

### Out of scope
- Delete functionality (covered in T04)
- Confirmation modal (covered in T04)
- Advanced filtering or sort controls
- Real-time search or debouncing
- Error boundary or retry logic (basic error display only)

## Dependencies
- Depends on: T02 (requires search API endpoint)
- Unblocks: T04 (delete functionality builds on this UI)

## Implementation plan
1. Update `vulcanlab_ui/src/components/nav-bar.tsx`:
   - Add new nav item to navItems array above Settings entry
   - Use object: `{ href: "/cleanup", label: "Cleanup", icon: Trash2, alwaysVisible: true }`
   - Import Trash2 icon from lucide-react
   - Position in array before Settings item
2. Create `vulcanlab_ui/src/app/cleanup/page.tsx`:
   - Mark as "use client" (needs interactivity)
   - Import necessary components: Button, Input, Card, Badge from @/components/ui
   - Import icons: Search, ChevronLeft, ChevronRight from lucide-react
3. Implement component state:
   - useState for: searchQuery, results, pagination, loading, error
   - pagination state: { page, totalResults, hasNext, hasPrev }
4. Implement search form:
   - Text input with placeholder "Search chunks by title or content..."
   - Search button with Search icon
   - Handle form submission (prevent default, call search API)
   - Clear button to reset search (optional but helpful)
5. Implement handleSearch function:
   - Set loading=true
   - Call fetch to GET /api/v1/chunks/search?q={query}&page={page}
   - Parse JSON response
   - Update results and pagination state
   - Set loading=false
   - Handle errors with error state (display user-friendly message)
6. Implement results display:
   - Map over results array to render chunk cards
   - Each card shows:
     - Heading breadcrumbs at top (if exists) in muted text
     - Content preview (100 chars) in regular text
     - Metadata row: Level badge + Work ID + Line range
   - Use Card component for each result
   - Use Badge component for level (with variant based on level type)
7. Implement pagination controls:
   - Previous button: disabled when !hasPrev, onClick decrements page and re-searches
   - Next button: disabled when !hasNext, onClick increments page and re-searches
   - Page indicator: "Page {page}" or "Showing {start}-{end} of {total} results"
   - Position controls at bottom of results
8. Implement empty states:
   - Initial state (before first search): "Enter a search term to find chunks"
   - No results state (after search with 0 results): "No chunks found matching '{query}'"
   - Use centered layout with muted text
9. Layout structure:
   - Page title: "Chunk Cleanup" with Trash2 icon
   - Description: "Search and remove unwanted chunks from the database"
   - Search form section
   - Results section (conditional rendering based on state)
   - Pagination section (only show if results exist)
10. Styling:
    - Use TailwindCSS utility classes
    - Consistent spacing with padding/margin utilities
    - Responsive layout (mobile-friendly)
    - Match existing VulcanLab UI patterns

- Patterns to apply:
  - **Next.js App Router**: Use `vulcanlab_ui/src/app/cleanup/page.tsx` structure
  - **Client components**: Mark with "use client" for interactivity
  - **Component reuse**: Use existing UI components from `@/components/ui`
  - **TailwindCSS**: Use utility classes for styling
  - **Naming conventions**: PascalCase for component, kebab-case for route

- Deviations (if any):
  - None: Fully aligned with patterns.md

## Unit tests (required)
- Add tests for:
  - **test_cleanup_nav_link_exists**: Verify "Cleanup" link appears in nav-bar above Settings
  - **test_cleanup_nav_link_always_visible**: Verify alwaysVisible=true for Cleanup nav item
  - **test_cleanup_page_renders**: Verify page renders without crashing
  - **test_search_form_submission**: Mock fetch, submit form, verify API called with correct params
  - **test_search_results_display**: Mock API response, verify results render with correct data
  - **test_heading_breadcrumbs_display**: Mock result with breadcrumbs, verify displayed at top
  - **test_content_preview_display**: Mock result with content, verify truncated content displayed
  - **test_level_badge_display**: Mock result, verify level badge renders
  - **test_pagination_next_button**: Mock results with hasNext=true, verify Next button enabled
  - **test_pagination_prev_button**: Mock results with hasPrev=false on page 1, verify Prev button disabled
  - **test_pagination_button_click**: Click Next, verify page increments and search re-called
  - **test_empty_state_initial**: Verify empty state message before first search
  - **test_empty_state_no_results**: Mock empty results, verify "No chunks found" message
  - **test_loading_state**: Verify loading indicator shows during fetch
  - **test_error_state**: Mock fetch error, verify error message displayed

- Suggested locations:
  - `tests/unit/test_cleanup_page.tsx` (new file, React Testing Library)
  - `tests/unit/test_nav_bar.tsx` (update existing if it exists)

- Mocking/fakes needed:
  - Mock global fetch API
  - Mock API responses for search endpoint
  - React Testing Library for component testing
  - Mock useRouter if navigation testing is needed

## Acceptance criteria (checklist)
- [ ] "Cleanup" link appears in nav bar above Settings with Trash2 icon
- [ ] Cleanup nav link is always visible (not restricted to advanced mode)
- [ ] Clicking Cleanup link navigates to /cleanup page
- [ ] Page displays title "Chunk Cleanup" with description
- [ ] Search form has text input and search button
- [ ] Initial page shows empty state with search instructions
- [ ] Submitting search calls GET /api/v1/chunks/search with correct parameters
- [ ] Search results display as cards with all required metadata
- [ ] Heading breadcrumbs display at top of card (when present)
- [ ] Content preview truncated to 100 characters
- [ ] Level badge displays with appropriate styling
- [ ] Work ID and line range display correctly ("Lines X-Y")
- [ ] Pagination controls show Previous and Next buttons
- [ ] Previous button disabled on page 1
- [ ] Next button disabled on last page
- [ ] Clicking pagination buttons re-fetches with new page number
- [ ] Page indicator shows current page or result range
- [ ] Empty results show "No chunks found" message
- [ ] Loading state shows while fetching
- [ ] Error state displays user-friendly message on fetch failure
- [ ] All unit tests pass

## Manual verification
- Steps:
  1. Run Next.js dev server: `npm run dev` in vulcanlab_ui
  2. Open http://localhost:3000 in browser
  3. Verify "Cleanup" link appears in nav bar above Settings
  4. Click "Cleanup" link
  5. Verify page displays with title, description, and search form
  6. Verify empty state message displays
  7. Enter search term "test" and click Search
  8. Verify results display with cards showing metadata
  9. Verify heading breadcrumbs appear at top of each card
  10. Verify content preview is truncated
  11. Verify level badge, work ID, and line range display
  12. Click Next button (if available)
  13. Verify page 2 results load
  14. Verify Previous button becomes enabled
  15. Click Previous button
  16. Verify page 1 results return
  17. Search for non-existent term
  18. Verify "No chunks found" message displays
  19. Test responsive layout on mobile viewport

- Expected results:
  - Navigation works correctly
  - Search executes and displays results
  - Pagination works in both directions
  - Empty states display appropriately
  - All metadata displays correctly formatted
  - UI matches existing VulcanLab design patterns
  - Page is responsive and mobile-friendly

## Notes
- This ticket creates the first end-to-end vertical slice: users can search and view chunks
- Delete functionality (with modal) is intentionally deferred to T04 to keep tickets focused
- API endpoint from T02 must be complete before this ticket can be tested end-to-end
- Use environment variable or config for API base URL (likely already configured in project)
- For content preview truncation, consider adding "..." suffix if truncated
- Level badge colors: consider using different variants/colors for H1-H5, sentence, chunk levels
- Line range format: "Lines {start_line}-{end_line}"
- Heading breadcrumbs: display in muted/secondary text to differentiate from content
- Search button: consider disabling when query is empty to prevent unnecessary API calls
- Loading state: use existing loading spinner or skeleton components if available
- Consider adding keyboard support (Enter key to submit search)
- Results should maintain scroll position when paginating (or scroll to top)
- Error handling: display errors from API (like "Search query cannot be empty" for 400 responses)
