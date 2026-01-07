# Ticket: corpus-search-feature.T01 - Lexical Search Backend and Basic UI

## Source

* Spec: documentation/work/corpus-search-feature.spec.md
* Patterns: documentation/patterns.md

## Goal

* Implement lexical (full-text) search backend using PostgreSQL ts_vector/ts_query
* Create breadcrumb generation by traversing chunk hierarchy to H1
* Build basic search UI with query input, lexical-only mode, and result display
* Add "Search" navigation item above "Cleanup"

## Scope

### In scope

* Core module: `src/vulcanlab/search/search_lexical.py` for PostgreSQL FTS queries
* Core module: `src/vulcanlab/search/breadcrumb_builder.py` for hierarchy traversal
* API router: `src/vulcanlab_api/routers/search.py` with `GET /api/v1/search/lexical` endpoint
* Frontend: `/search` page with basic query input and lexical search mode
* Frontend: Navigation bar update to add "Search" item above "Cleanup"
* Frontend: Search result cards displaying breadcrumbs, bibliographic info, content preview, metadata
* Pagination for search results (matching cleanup pattern)
* Unit tests for lexical search and breadcrumb generation

### Out of scope

* Dense search (T02)
* Hybrid search with RRF fusion (T03)
* Advanced UI controls (RRF parameters, dense/hybrid modes) (T04)
* Document viewer with highlighting (T05)
* Query expansion or reranking
* Search result persistence

## Dependencies

* Depends on: none
* Unblocks: T02, T03, T04, T05

## Implementation plan

1. Create `src/vulcanlab/search/__init__.py` module
2. Implement `src/vulcanlab/search/breadcrumb_builder.py`:
   - Function `build_breadcrumb(chunk_id: int, session: Session) -> str`
   - Traverse `chunks.parent_id` recursively up to H1 or root
   - Return formatted breadcrumb string (e.g., "Chapter 1 > Section 1.2 > Subsection 1.2.3")
   - Handle orphaned chunks by returning "[No heading]"
3. Implement `src/vulcanlab/search/search_lexical.py`:
   - Function `search_lexical(query: str, session: Session, page: int, page_size: int, headings_only: bool, top_k: int) -> tuple[list[dict], int]`
   - Use `to_tsvector(content) @@ to_tsquery(query)` for FTS
   - Order by `ts_rank(to_tsvector(content), to_tsquery(query)) DESC`
   - If `headings_only=True`, filter to `level IN ('H1', 'H2', 'H3', 'H4', 'H5')`
   - JOIN with `works` table to fetch bibliographic info (title, authors, year)
   - Call `build_breadcrumb()` for each result
   - Return paginated results with metadata
4. Create `src/vulcanlab_api/routers/search.py`:
   - Define Pydantic response models: `SearchResult`, `PaginationInfo`
   - Implement `GET /api/v1/search/lexical` endpoint
   - Validate query parameters (q, page, page_size, headings_only, top_k)
   - Call `search_lexical()` from core module
   - Return JSON response with results and pagination info
   - Log search parameters at INFO level, execution time at DEBUG level
5. Register router in `src/vulcanlab_api/main.py` with prefix `/api/v1/search`
6. Update `vulcanlab_ui/src/components/nav-bar.tsx`:
   - Add new nav item `{ href: "/search", label: "Search", icon: Search, alwaysVisible: true }`
   - Position it before the "Cleanup" item in the navItems array
7. Create `vulcanlab_ui/src/app/search/page.tsx`:
   - "use client" component with search form (query input, "Search" button)
   - Checkbox for "Headings only (H1-H5)"
   - Use `useCallback` for fetch function to avoid infinite loops
   - Use `usePageData` hook pattern for data fetching
   - Display `PageLoadingState`, `PageErrorState`, and `EmptyState` as appropriate
   - Render search result cards showing: breadcrumb, bibliographic info (title, author, year), content preview (first 100 words), metadata (level badge, work_id, lines, chunk_id)
   - Implement pagination controls (prev/next buttons) matching cleanup pattern
8. Add unit tests in `tests/unit/test_search_lexical.py`:
   - Mock database session
   - Test single-word query, multi-word query, phrase query
   - Test headings_only filter excludes sentence/paragraph chunks
   - Test pagination edge cases (first page, last page, out of range)
9. Add unit tests in `tests/unit/test_breadcrumb_builder.py`:
   - Mock database session with chunk hierarchy
   - Test breadcrumb generation for chunks at various depths
   - Test orphaned chunk returns "[No heading]"
   - Test root chunk (H1 with no parent)

* Patterns to apply:
  * Three-tier architecture - Core logic in `src/vulcanlab/search/`, API in `src/vulcanlab_api/routers/search.py`, UI in `vulcanlab_ui/src/app/search/`
  * Core module independence - No FastAPI imports, session passed as argument
  * API versioning - Endpoint uses `/api/v1/search/lexical` prefix
  * Global exception handling - API raises HTTPException, lets middleware handle errors
  * Page lifecycle pattern - Search page uses `usePageData` with memoized fetch function
  * Component composition - Reuse `PageLoadingState`, `PageErrorState`, `EmptyState`
  * Theme awareness - Use Tailwind semantic classes
  * Database session management - Session passed explicitly to search functions

* Deviations (if any):
  * None

## Unit tests (required)

* Add tests for:
  * Lexical search with single word query returns ranked results
  * Lexical search with multi-word query returns ranked results
  * Lexical search with phrase query returns ranked results
  * Headings only filter excludes chunks with level='sentence' or 'paragraph'
  * Headings only filter includes chunks with level='H1', 'H2', 'H3', 'H4', 'H5'
  * Pagination calculates offset correctly: (page - 1) * page_size
  * Pagination returns has_next=true when more results exist
  * Pagination returns has_prev=false on page 1
  * Breadcrumb generation traverses hierarchy to H1
  * Breadcrumb generation handles orphaned chunks (returns "[No heading]")
  * Breadcrumb generation handles root chunks (H1 with parent_id=NULL)
  * Search joins with works table and includes bibliographic metadata
  * Content preview truncates to word limit (100 words default)

* Suggested locations:
  * `tests/unit/test_search_lexical.py`
  * `tests/unit/test_breadcrumb_builder.py`

* Mocking/fakes needed:
  * Mock SQLAlchemy session with query results
  * Mock chunks table with hierarchy (parent_id relationships)
  * Mock works table with bibliographic data
  * Mock embeddings table (not used in this ticket, but exists in schema)

## Acceptance criteria (checklist)

* [ ] "Search" nav item appears above "Cleanup" in navigation bar and is clickable
* [ ] Search page renders at `/search` with query input and "Headings only" checkbox
* [ ] Lexical search endpoint `GET /api/v1/search/lexical` returns results with ts_rank scores
* [ ] Search results display breadcrumbs generated by traversing hierarchy to H1
* [ ] Orphaned chunks display "[No heading]" as breadcrumb
* [ ] Search results display bibliographic info (work title, author, year)
* [ ] Search results display content preview (first 100 words)
* [ ] Search results display metadata (level badge, work_id, lines, chunk_id)
* [ ] "Headings only" filter excludes non-heading chunks (sentence, paragraph)
* [ ] Pagination controls work correctly (prev/next buttons disabled appropriately)
* [ ] Unit tests pass with >80% coverage for lexical search and breadcrumb modules
* [ ] Backend logs search parameters at INFO level
* [ ] Backend logs execution time at DEBUG level

## Manual verification

* Steps:
  1. Start the backend API and frontend dev server
  2. Navigate to the application in browser
  3. Verify "Search" appears in nav bar above "Cleanup"
  4. Click "Search" to navigate to `/search`
  5. Enter a single-word query (e.g., "memory") and click "Search"
  6. Verify results appear with breadcrumbs, bibliographic info, content preview, metadata
  7. Check "Headings only" checkbox and search again
  8. Verify only H1-H5 chunks appear in results
  9. Navigate through multiple pages using prev/next buttons
  10. Verify pagination state updates correctly
  11. Check backend logs for search parameters and execution time

* Expected results:
  * "Search" nav item visible and functional
  * Search page renders without errors
  * Lexical search returns ranked results ordered by ts_rank
  * Breadcrumbs show hierarchical path (e.g., "Chapter 1 > Section 1.2")
  * Orphaned chunks show "[No heading]"
  * Bibliographic info displays correctly (title, author, year)
  * Content preview truncates at 100 words
  * Headings only filter excludes sentence/paragraph chunks
  * Pagination controls navigate correctly through result pages
  * Logs contain search parameters and timing information

## Notes

* Requirements covered: R1, R2, R3 (lexical mode only), R6, R7 (100 word default), R8, R9, R14, R16, R18, R19
* This ticket establishes the walking skeleton for the search feature
* Lexical search uses PostgreSQL's built-in full-text search (no external dependencies)
* Breadcrumb generation may be slow for deep hierarchies; consider caching in future iteration
* Content preview word limit is hardcoded to 100 words in this ticket; T04 will add UI control
* Search mode selection UI (lexical/dense/both) deferred to T04; this ticket only implements lexical
* Result cards should follow cleanup's visual pattern but add bibliographic metadata
* Use recursive CTE or iterative query for breadcrumb traversal (prefer CTE for performance)
* Ensure fetch function in search page is wrapped in useCallback to prevent infinite loops
