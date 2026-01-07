# Ticket: corpus-search-feature.T04 - Search UI Enhancements and Controls

## Source

* Spec: documentation/work/corpus-search-feature.spec.md
* Patterns: documentation/patterns.md

## Goal

* Enhance search UI with proper search mode selection (checkboxes for lexical/dense/both)
* Add collapsible RRF parameter controls (k, top-k, weights)
* Add max preview word count slider
* Improve result card layout with better metadata display

## Scope

### In scope

* Frontend: Enhanced search mode selection (checkboxes: Lexical, Dense, or both)
* Frontend: Collapsible RRF settings panel (k constant, dense top-k, lexical top-k, weights)
* Frontend: Max preview words slider (50-500 range, default 100)
* Frontend: Improved result card design with bibliographic metadata
* Frontend: Content preview truncation based on word limit
* Unit tests for UI components (if using testing library)

### Out of scope

* Backend changes (all endpoints already implemented in T01-T03)
* Document viewer (T05)
* Advanced filters (date ranges, author filtering)
* Search history or saved searches

## Dependencies

* Depends on: T01, T02, T03
* Unblocks: T05

## Implementation plan

1. Update `vulcanlab_ui/src/app/search/page.tsx`:
   - Replace simple toggle with checkboxes: "Lexical Search", "Dense Search"
   - Add state: `const [lexicalEnabled, setLexicalEnabled] = useState(true); const [denseEnabled, setDenseEnabled] = useState(false);`
   - Determine search mode: if both enabled -> hybrid, if only one -> that mode, if neither -> disable search button
   - Add collapsible "Advanced Settings" panel (use Accordion or Collapsible from shadcn)
   - Inside advanced panel, add RRF controls (shown only when both modes enabled):
     - Number input for RRF k constant (default 60, min 1, max 200)
     - Number input for Dense top-k (default 20, min 1, max 100)
     - Number input for Lexical top-k (default 20, min 1, max 100)
     - Slider or number inputs for weights (Dense weight, Lexical weight, default 0.5 each)
   - Add "Max preview words" slider outside advanced panel (range 50-500, default 100, step 10)
   - Update fetch logic to call appropriate endpoint based on mode:
     - Both enabled -> `/api/v1/search/hybrid` with RRF params
     - Lexical only -> `/api/v1/search/lexical`
     - Dense only -> `/api/v1/search/dense`
   - Pass max preview words to result card component
2. Implement content preview truncation utility:
   - Function `truncateToWordLimit(content: string, maxWords: number): string`
   - Split content by whitespace, take first N words, join with spaces
   - Add "..." if truncated
   - Use per-chunk (not total across page)
3. Enhance result card component:
   - Create `SearchResultCard` component or inline render
   - Display breadcrumb at top (small muted text)
   - Display bibliographic info: work title (bold), author, year (if available)
   - Display content preview (truncated to max preview words)
   - Display metadata row: level badge, work_id, lines (start_line-end_line), chunk_id
   - Display score(s): RRF score for hybrid, similarity score for dense, ts_rank for lexical
   - Display rank badges for hybrid: dense_rank, lexical_rank
   - Use theme-aware Tailwind classes
   - Add hover effect for better UX
4. Add validation and error handling:
   - Disable search button if no mode selected
   - Show warning if RRF weights are both 0 (invalid)
   - Validate top-k and k values (must be >= 1)
   - Display error message if search fails
5. Add unit tests (if using React Testing Library):
   - Test search mode checkboxes toggle correctly
   - Test search button disabled when no mode selected
   - Test advanced settings panel toggles open/closed
   - Test RRF controls appear only when both modes enabled
   - Test max preview words slider updates state
   - Test content truncation utility with various word counts
   - Test result card renders all fields correctly
   - Mock fetch and test API calls with correct parameters

* Patterns to apply:
  * Page lifecycle pattern - Use usePageData hook with memoized fetch function
  * Component composition - Create SearchResultCard component for reusability
  * Theme awareness - Use Tailwind semantic classes (text-foreground, bg-card, etc.)
  * Avoid infinite loops - Wrap fetch function in useCallback with proper dependencies

* Deviations (if any):
  * None

## Unit tests (required)

* Add tests for:
  * Search mode checkboxes: both enabled triggers hybrid search
  * Search mode checkboxes: only lexical enabled triggers lexical search
  * Search mode checkboxes: only dense enabled triggers dense search
  * Search mode checkboxes: neither enabled disables search button
  * Advanced settings panel opens and closes correctly
  * RRF controls (k, top-k, weights) appear when both modes enabled
  * RRF controls hidden when only one mode enabled
  * Max preview words slider updates state correctly
  * Content truncation: truncateToWordLimit(100 words, 50) returns 50 words + "..."
  * Content truncation: truncateToWordLimit(30 words, 50) returns 30 words (no truncation)
  * SearchResultCard renders breadcrumb, bibliographic info, preview, metadata
  * SearchResultCard displays correct score based on search mode
  * SearchResultCard displays rank badges for hybrid results

* Suggested locations:
  * `vulcanlab_ui/src/app/search/__tests__/page.test.tsx` (if using testing library)
  * `vulcanlab_ui/src/utils/__tests__/truncate.test.ts` (for truncation utility)

* Mocking/fakes needed:
  * Mock fetch API responses
  * Mock usePageData hook (if testing component in isolation)

## Acceptance criteria (checklist)

* [ ] Search mode selection uses checkboxes (Lexical, Dense)
* [ ] Both checkboxes enabled triggers hybrid search with RRF
* [ ] One checkbox enabled triggers corresponding single-mode search
* [ ] Search button disabled when no mode selected
* [ ] Advanced settings panel toggles open/closed
* [ ] RRF controls (k, top-k, weights) appear only when both modes enabled
* [ ] Max preview words slider controls preview length (50-500 range)
* [ ] Content preview truncates to word limit per-chunk
* [ ] Result cards display breadcrumb, bibliographic info, preview, metadata
* [ ] Result cards show appropriate score(s) based on search mode
* [ ] Hybrid results show both dense_rank and lexical_rank badges
* [ ] RRF parameters passed correctly to hybrid search endpoint
* [ ] UI is theme-aware (dark/light mode)
* [ ] Unit tests pass for UI components and utilities

## Manual verification

* Steps:
  1. Navigate to `/search` in browser
  2. Verify checkboxes for "Lexical Search" and "Dense Search" are present
  3. Check only "Lexical" checkbox and search -> verify lexical endpoint called
  4. Check only "Dense" checkbox and search -> verify dense endpoint called
  5. Check both checkboxes and search -> verify hybrid endpoint called
  6. Uncheck both checkboxes -> verify search button disabled
  7. With both enabled, expand "Advanced Settings" panel
  8. Verify RRF controls appear: k constant, dense top-k, lexical top-k, weights
  9. Adjust RRF k value and search -> verify parameter passed to API
  10. Adjust max preview words slider -> verify preview length changes in results
  11. Test with slider at 50 words -> verify short previews
  12. Test with slider at 500 words -> verify long previews
  13. Verify result cards show breadcrumb, bibliographic info, truncated preview, metadata
  14. Verify hybrid results show both dense and lexical rank badges
  15. Toggle dark mode -> verify UI remains theme-aware

* Expected results:
  * Search mode checkboxes control which endpoint is called
  * Hybrid mode triggers when both checkboxes enabled
  * Search button disabled when no mode selected
  * Advanced settings panel reveals RRF controls
  * RRF controls only appear when both modes enabled
  * Max preview words slider changes preview length dynamically
  * Content truncates at word boundaries (not character boundaries)
  * Result cards display all required metadata clearly
  * Hybrid results show rank badges for both methods
  * UI adapts to theme (dark/light mode)

## Notes

* Requirements covered: R3, R5, R6 (already implemented in T01, UI control added here), R7, R8
* This ticket focuses on UI polish and user-facing controls
* RRF weight sliders could be percentage-based (0-100%) for better UX
* Weight normalization happens in backend (T03), but UI could show normalized values
* Max preview words applies per-chunk (not total across page)
* Consider adding tooltip or help text for RRF parameters (explain what they do)
* Collapsible advanced settings prevents UI clutter for basic users
* Default values should match backend defaults (k=60, top_k=20, weights=0.5)
* Content truncation should preserve whole words (not cut mid-word)
* Result card design should be consistent with cleanup page pattern
