# Title: Chunk Cleanup UI

## Summary
- Add a new "Cleanup" page accessible from the navigation that allows users to search and delete unwanted chunks from the RAG database
- Implement lexical search functionality that searches both chunk content and extracted heading titles
- Display paginated search results with chunk metadata and provide delete capability with cascading child deletion
- When deleting a chunk, show a warning modal listing all descendant chunks that will be deleted to prevent orphaned records
- Ensure database integrity by implementing recursive deletion of all child chunks at any depth level
- Include comprehensive unit tests to verify cascading deletion logic and prevent orphaned chunks

## Problem / Context
- Users currently have no way to remove unwanted or irrelevant chunks from the RAG system through the UI
- Chunks that should not be considered for retrieval remain in the database, potentially degrading RAG quality
- Manual database operations are risky and could leave orphaned child chunks if parent-child relationships are not properly handled
- The chunk table has hierarchical parent-child relationships (via `parent_id` foreign key) that must be maintained during deletion
- User impact: Cannot curate or clean their RAG corpus, leading to lower quality retrieval results
- Business impact: Reduces effectiveness of the RAG system and requires technical intervention for chunk management

## Goals
- Provide a UI page for searching and deleting chunks from the database
- Implement lexical search that searches both content and heading titles with appropriate ranking
- Display search results with relevant metadata in a paginated view
- Implement safe cascading deletion that removes all descendant chunks at any level
- Warn users about child chunks that will be deleted before confirming deletion
- Maintain database referential integrity by preventing orphaned chunks

## Non-goals (Strict)
- Real-time search or auto-complete functionality
- Bulk deletion of multiple chunks in a single operation
- Undo/restore functionality for deleted chunks
- Filtering by work, corpus, or other metadata fields
- Export or archive of deleted chunks
- User authentication or role-based access control for deletion
- Audit logging or deletion history tracking
- Editing or modifying chunk content (only deletion)
- Preview of how deletion affects RAG results

## Scope
### In scope
- New `/cleanup` page in the Next.js UI with navigation link
- Search form with single text input for lexical search
- Backend API endpoint for searching chunks (lexical search on content and title)
- Backend API endpoint for deleting chunks with cascading child deletion
- Paginated results display (25 per page) showing chunk metadata
- Delete button (garbage icon) on each search result
- Confirmation modal showing all descendant chunks before deletion
- Unit tests for cascading deletion logic
- UI feedback for successful/failed deletion operations

### Out of scope
- Filtering by work_id, corpus_id, level, or other fields
- Bulk operations (select multiple, delete all, etc.)
- Soft delete or trash/recycle bin functionality
- Deletion audit log or history
- Authorization/access control mechanisms
- Pagination controls beyond basic next/prev
- Advanced search (regex, boolean operators, field-specific queries)
- Sort controls or result ordering options beyond the specified ranking

## Requirements (Functional)
- R1: Navigation must include a "Cleanup" link positioned above "Settings" in the nav bar, always visible (not restricted to advanced mode)
- R2: Search must perform lexical search on chunk `content` field and extracted heading title from `heading_breadcrumbs`
- R3: Search results must be ordered with title matches first (exact matches, then partial matches), followed by content matches ordered by relevance
- R4: Each search result must display: heading_breadcrumbs (if exists), content preview (first 100 characters), level, work_id, and line range (start_line-end_line)
- R5: Results must be paginated at 25 chunks per page with next/previous navigation
- R6: Each result must have a delete button (garbage/trash icon) that triggers the deletion flow
- R7: Clicking delete must open a confirmation modal listing ALL descendant chunks (all generations) with their levels, ids, and heading breadcrumbs
- R8: Deletion must recursively delete the selected chunk and ALL descendant chunks at any depth level
- R9: Database must enforce `ondelete="CASCADE"` behavior (already exists in schema) to prevent orphaned records
- R10: After successful deletion, the deleted chunk must be removed from the current search results view without re-running the query
- R11: If deletion fails, display an error message and keep the chunk in the results
- R12: Empty search or initial page load must show empty state with instructions to enter a search query

## Requirements (Non-functional)
- Performance:
  - Search queries must complete within 2 seconds for databases with up to 100,000 chunks
  - Deletion operations must complete within 5 seconds regardless of descendant count
  - Pagination must not load all results into memory (use SQL LIMIT/OFFSET)
- Reliability:
  - Cascading deletion must be transactional (all-or-nothing via database transaction)
  - If cascading deletion fails partway through, entire operation must roll back
  - Search must handle special characters and SQL injection attempts safely (use parameterized queries)
- Security / Privacy:
  - API endpoints must use existing authentication mechanisms (if any)
  - No authorization layer needed (any authenticated user can delete)
  - Input sanitization for search queries to prevent injection attacks
- Observability:
  - Deletion operations should log chunk_id and descendant count at INFO level
  - Failed deletions should log error details at ERROR level
  - Search errors should be logged but not exposed to user

## Proposed Solution (High-level)
- Add new route `/cleanup` in Next.js app router (`vulcanlab_ui/src/app/cleanup/page.tsx`)
- Create a client component for the search form and results display
- Add "Cleanup" nav item to `nav-bar.tsx` above Settings with Trash2 or Database icon from lucide-react
- Implement FastAPI router at `/api/v1/chunks/search` (GET) for lexical search
  - Accept query parameter `q` (search term) and `page` (default 1)
  - Search `content` field using PostgreSQL full-text search or `ILIKE`
  - Extract last heading from `heading_breadcrumbs` by splitting on " > " and taking last element
  - Search extracted title using `ILIKE`
  - Rank results: exact title matches first, then partial title matches, then content matches
  - Return paginated results with total count, current page, and has_next/has_prev flags
- Implement FastAPI router at `/api/v1/chunks/{chunk_id}` (DELETE) for deletion
  - Accept chunk_id as path parameter
  - Return list of all descendant chunks before deletion (for modal display)
  - Perform recursive query to find all descendants using recursive CTE or iterative traversal
  - Delete chunk (CASCADE will handle descendants automatically via FK constraint)
  - Use database transaction to ensure atomicity
- Implement core deletion logic in `src/vulcanlab/data/chunk_operations.py`
  - Function: `get_all_descendants(chunk_id: int, session: Session) -> List[Chunk]`
  - Function: `delete_chunk_cascade(chunk_id: int, session: Session) -> int` (returns count deleted)
- UI components:
  - Search form with text input and search button
  - Results list showing chunk cards with metadata and delete icon
  - Confirmation dialog using Radix AlertDialog showing descendant list
  - Pagination controls (Previous/Next buttons, page indicator)
  - Empty state for no results or initial load

## Interfaces / APIs / Contracts

### API Endpoints

**GET /api/v1/chunks/search**
- Query Parameters:
  - `q` (string, required): Search query term
  - `page` (integer, optional, default=1): Page number for pagination
- Response (200 OK):
  ```json
  {
    "results": [
      {
        "id": 123,
        "content_preview": "First 100 characters of content...",
        "heading_breadcrumbs": "Chapter 1 > Section 1.1 > Subsection 1.1.1",
        "level": "H3",
        "work_id": 42,
        "start_line": 100,
        "end_line": 150
      }
    ],
    "pagination": {
      "page": 1,
      "page_size": 25,
      "total_results": 47,
      "has_next": true,
      "has_prev": false
    }
  }
  ```
- Error Response (400 Bad Request): `{"detail": "Search query cannot be empty"}`
- Error Response (500 Internal Server Error): `{"detail": "Search failed"}`

**DELETE /api/v1/chunks/{chunk_id}**
- Path Parameters:
  - `chunk_id` (integer, required): ID of chunk to delete
- Response (200 OK):
  ```json
  {
    "deleted_chunk_id": 123,
    "descendants_deleted": [
      {
        "id": 124,
        "level": "H4",
        "heading_breadcrumbs": "Chapter 1 > Section 1.1 > Subsection 1.1.1 > Topic A"
      },
      {
        "id": 125,
        "level": "sentence",
        "heading_breadcrumbs": "Chapter 1 > Section 1.1 > Subsection 1.1.1 > Topic A"
      }
    ],
    "total_deleted": 3
  }
  ```
- Error Response (404 Not Found): `{"detail": "Chunk not found"}`
- Error Response (500 Internal Server Error): `{"detail": "Deletion failed"}`

**GET /api/v1/chunks/{chunk_id}/descendants** (for modal preview)
- Path Parameters:
  - `chunk_id` (integer, required): ID of chunk to preview descendants
- Response (200 OK):
  ```json
  {
    "descendants": [
      {
        "id": 124,
        "level": "H4",
        "heading_breadcrumbs": "Chapter 1 > Section 1.1 > Subsection 1.1.1 > Topic A"
      }
    ],
    "total_count": 1
  }
  ```

### Core Module Functions

**vulcanlab.data.chunk_operations.get_all_descendants**
```python
def get_all_descendants(chunk_id: int, session: Session) -> List[Chunk]:
    """
    Recursively retrieve all descendant chunks at any depth.

    Args:
        chunk_id: ID of parent chunk
        session: SQLAlchemy database session

    Returns:
        List of all descendant Chunk objects (all generations)
    """
```

**vulcanlab.data.chunk_operations.delete_chunk_cascade**
```python
def delete_chunk_cascade(chunk_id: int, session: Session) -> int:
    """
    Delete a chunk and all its descendants in a transaction.

    Args:
        chunk_id: ID of chunk to delete
        session: SQLAlchemy database session

    Returns:
        Total number of chunks deleted (including descendants)

    Raises:
        ValueError: If chunk_id does not exist
        SQLAlchemyError: If deletion fails
    """
```

**vulcanlab.data.chunk_operations.search_chunks_lexical**
```python
def search_chunks_lexical(
    query: str,
    page: int,
    page_size: int,
    session: Session
) -> Tuple[List[Chunk], int]:
    """
    Search chunks by content and extracted title with custom ranking.

    Args:
        query: Search term
        page: Page number (1-indexed)
        page_size: Number of results per page
        session: SQLAlchemy database session

    Returns:
        Tuple of (list of matching chunks, total result count)

    Ranking:
        1. Exact title matches
        2. Partial title matches
        3. Content matches (by relevance)
    """
```

## Data Model / Storage
- Uses existing `chunks` table (no schema changes required)
- Existing schema already has:
  - `parent_id` with `ondelete="CASCADE"` for automatic child deletion
  - Appropriate indexes on `parent_id`, `work_id`, `level`, and `vector_status`
- No new tables or migrations needed
- Deletion relies on PostgreSQL CASCADE behavior via foreign key constraint

## UX / Workflows

### Search Flow
1. User navigates to `/cleanup` from nav bar
2. Initial page shows empty state with search instructions
3. User enters search term in text input and clicks "Search" button
4. Results load showing paginated list of matching chunks
5. Each result displays as a card with heading breadcrumbs (if exists) at top, content preview, level badge, work_id, and line range
6. User can navigate between pages using Previous/Next buttons
7. Page indicator shows "Page X of Y" or "Showing 1-25 of 47 results"

### Deletion Flow
1. User clicks garbage/trash icon on a chunk result card
2. System fetches all descendants via API call
3. Confirmation modal opens with:
   - Warning message: "This will permanently delete this chunk and all its descendants"
   - List of descendants showing: id, level, and heading_breadcrumbs
   - Total count: "X chunks will be deleted"
   - Cancel and Confirm Delete buttons
4. User clicks Cancel: modal closes, no action taken
5. User clicks Confirm Delete:
   - Loading indicator shows on modal
   - DELETE API call executes
   - On success: modal closes, chunk removed from results list, success toast appears
   - On failure: error message displayed in modal, chunk remains in results
6. User can continue searching and deleting other chunks

## Testing Plan

### Unit tests
- **test_get_all_descendants**: Verify recursive retrieval of descendants
  - Create chunk tree: parent -> child -> grandchild -> great-grandchild
  - Call `get_all_descendants(parent.id)` and verify all 3 descendants returned
  - Test single-level children (no grandchildren)
  - Test chunk with no children returns empty list
  - Test non-existent chunk_id behavior
- **test_delete_chunk_cascade**: Verify cascading deletion
  - Create chunk tree with multiple levels
  - Delete parent and verify all descendants deleted from database
  - Verify correct count returned
  - Test deletion of leaf node (no children) works correctly
  - Test database transaction rollback on deletion failure
- **test_search_chunks_lexical_title_ranking**: Verify title search and ranking
  - Create chunks with heading_breadcrumbs containing "Reference"
  - Search for "Reference" and verify exact title matches appear first
  - Create chunks with partial matches and verify ordering
  - Test case-insensitive matching
- **test_search_chunks_lexical_content_ranking**: Verify content search
  - Create chunks with search term in content
  - Verify content matches appear after title matches
  - Test pagination with page_size=25
  - Test empty results for non-matching query
- **test_search_pagination**: Verify pagination logic
  - Create 50 chunks, search, verify page 1 has 25 results
  - Verify page 2 has 25 results
  - Verify total_count is 50
  - Verify has_next and has_prev flags are correct
- **test_orphan_prevention**: Critical test for database integrity
  - Create parent with children and grandchildren
  - Attempt to delete parent with CASCADE disabled (simulate failure)
  - Verify error is raised
  - Verify no chunks are deleted (transaction rollback)
  - Re-enable CASCADE, delete parent, verify all descendants deleted

### Integration tests
- Not required for this ticket (unit tests sufficient for core logic)

### Manual test plan
- [ ] Navigate to Cleanup page from nav bar link
- [ ] Verify empty state displays on initial load
- [ ] Enter search term and verify results display correctly
- [ ] Verify heading_breadcrumbs displays at top of each card when present
- [ ] Verify content preview truncates at 100 characters
- [ ] Verify level badge and work_id display correctly
- [ ] Verify line range shows as "Lines X-Y" format
- [ ] Test pagination: navigate to next page and verify results change
- [ ] Test pagination: verify Previous button disabled on page 1
- [ ] Test pagination: verify Next button disabled on last page
- [ ] Click delete icon and verify modal opens
- [ ] Verify modal lists all descendant chunks with correct details
- [ ] Verify modal shows total count of chunks to be deleted
- [ ] Click Cancel in modal and verify no deletion occurs
- [ ] Click Confirm Delete and verify chunk disappears from results
- [ ] Verify success toast appears after deletion
- [ ] Test deleting chunk with no children (modal shows "No descendants")
- [ ] Test deleting chunk with multiple levels of children
- [ ] Use database viewer to verify descendants were actually deleted
- [ ] Use database viewer to verify no orphaned chunks remain
- [ ] Test search with special characters (quotes, apostrophes, etc.)
- [ ] Test search with empty string (should show validation error or no results)
- [ ] Test search with very long query string
- [ ] Test deletion error handling by simulating database failure (optional)

## Acceptance Criteria (Checklist)
- [ ] "Cleanup" link appears in nav bar above Settings and is always visible
- [ ] Clicking Cleanup nav link navigates to `/cleanup` page
- [ ] Search form accepts text input and has a search button
- [ ] Search returns results ranked with title matches first (exact, then partial), then content matches
- [ ] Each result displays: heading_breadcrumbs (if exists), content preview (100 chars), level, work_id, line range
- [ ] Results are paginated at 25 per page with working Previous/Next buttons
- [ ] Each result has a visible delete icon (garbage/trash)
- [ ] Clicking delete icon opens a confirmation modal
- [ ] Modal lists all descendant chunks with id, level, and heading_breadcrumbs
- [ ] Modal shows total count of chunks that will be deleted
- [ ] Modal has Cancel and Confirm Delete buttons
- [ ] Confirming deletion removes chunk and all descendants from database
- [ ] After deletion, chunk is removed from current results view
- [ ] Success toast/message appears after successful deletion
- [ ] Error message displays if deletion fails
- [ ] Unit tests pass for `get_all_descendants` with multi-level hierarchies
- [ ] Unit tests pass for `delete_chunk_cascade` with verification of complete deletion
- [ ] Unit tests verify no orphaned chunks remain after any deletion operation
- [ ] Manual testing confirms no orphaned chunks exist in database after various deletion scenarios

## Rollout / Migration Plan
- No database migrations required (uses existing schema)
- No feature flags or gradual rollout needed
- Deploy steps:
  1. Deploy backend API changes first (new endpoints)
  2. Deploy frontend changes (new page and nav link)
  3. Verify in staging environment with test data
  4. Deploy to production
- No data migration or backfill needed
- No rollback considerations beyond standard code deployment rollback

## Risks and Alternatives

### Risks
- **Data loss**: Accidental deletion of large chunk trees cannot be undone
  - Mitigation: Clear confirmation modal showing all descendants before deletion
  - Mitigation: Consider adding soft delete in future iteration if needed
- **Performance**: Recursive descendant queries could be slow for very deep hierarchies
  - Mitigation: Database CASCADE handles deletion efficiently at DB level
  - Mitigation: Descendant fetching for modal preview uses indexed parent_id
- **UI state management**: Removing deleted chunk from results without re-query could cause pagination issues
  - Mitigation: Keep simple removal from current page, accept that totals may be slightly off
- **Concurrent deletion**: Two users deleting the same chunk simultaneously could cause errors
  - Mitigation: Database transaction and FK constraints prevent corruption
  - Mitigation: 404 error on already-deleted chunk is acceptable UX

### Alternatives considered
- **Soft delete**: Add `deleted_at` timestamp instead of hard delete
  - Rejected: Adds schema complexity and this feature is for permanent cleanup
  - Could be added later if undo functionality is needed
- **Bulk deletion**: Allow selecting multiple chunks to delete at once
  - Rejected: Out of scope for initial implementation, can be added later
  - Single-delete is safer and easier to test initially
- **Advanced filtering**: Add filters for work_id, level, date range, etc.
  - Rejected: Simple search is sufficient for initial use case
  - Filtering can be added incrementally based on user feedback
- **Recursive CTE for descendant fetch**: Use PostgreSQL recursive CTE instead of iterative approach
  - Could be implemented: More efficient for very deep trees
  - Decision: Start with simpler iterative approach, optimize if needed
- **Archive before delete**: Export chunks to JSON before deletion
  - Rejected: Out of scope, users can export entire database if needed

## Patterns and Standards Alignment (from documentation/patterns.md)

### Patterns applied
- **Three-tier architecture**: Core logic in `src/vulcanlab/data/chunk_operations.py`, API layer in `src/vulcanlab_api/routers/chunks.py`, UI in `vulcanlab_ui/src/app/cleanup`
- **Session management**: All database functions accept `session: Session` parameter, no internal session creation
- **API versioning**: New endpoints use `/api/v1` prefix defined in main.py router inclusion
- **Error handling**: Use specific exceptions (ValueError, HTTPException) and allow global handlers to catch unhandled errors
- **Component reuse**: Use existing Shadcn/Radix components (AlertDialog, Button, Card) from `vulcanlab_ui/src/components/ui/`
- **Next.js App Router**: New page at `vulcanlab_ui/src/app/cleanup/page.tsx`
- **Client components**: Use `"use client"` for interactive search form and delete actions
- **TailwindCSS**: Use utility classes for styling, consistent with existing UI patterns
- **Naming conventions**: `snake_case` for Python functions, `kebab-case` for Next.js route, `PascalCase` for React components

### Deviations (if any)
- None: This spec fully aligns with documented patterns

## Implementation Notes (Non-binding)
- Consider using PostgreSQL full-text search (`to_tsvector`, `to_tsquery`) instead of `ILIKE` for better performance on large datasets
- For title extraction from `heading_breadcrumbs`, handle None values gracefully (chunks without breadcrumbs)
- Use Python's `unittest.mock` to mock database sessions in unit tests
- Consider adding `data-testid` attributes to UI components for easier E2E testing in the future
- Lucide-react icons to consider: `Trash2`, `Database`, `Search`, `AlertTriangle` for various UI elements
- Toast notifications can use existing toast system (likely from Radix UI Toast or similar)
- The CASCADE deletion is already configured in the schema (`ForeignKey("chunks.id", ondelete="CASCADE")`), so database will handle recursive deletion automatically
- For descendant preview, limit display to first 50 descendants with "and X more..." if count exceeds 50 to avoid modal overload
- Consider debouncing search input in future iteration (not required for initial implementation)

## Open Questions
- None: All questions have been answered by user
