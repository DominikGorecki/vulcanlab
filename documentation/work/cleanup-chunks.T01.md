# Ticket: cleanup-chunks.T01 - Core Backend Logic for Chunk Search and Deletion

## Source
- Spec: documentation/work/cleanup-chunks.spec.md
- Patterns: documentation/patterns.md

## Goal
- Implement core module functions for lexical chunk search with title/content ranking
- Implement recursive descendant retrieval and cascading deletion functions
- Ensure all functions follow session-passing patterns and remain framework-independent
- Provide comprehensive unit test coverage for all edge cases and cascading deletion

## Scope
### In scope
- Create `src/vulcanlab/data/chunk_operations.py` module
- Implement `search_chunks_lexical()` with title extraction and custom ranking
- Implement `get_all_descendants()` for recursive descendant retrieval
- Implement `delete_chunk_cascade()` with transactional deletion
- Unit tests for all functions including multi-level hierarchies and edge cases
- Proper error handling (ValueError for non-existent chunks, SQLAlchemyError propagation)

### Out of scope
- API endpoint implementation (covered in T02)
- UI components (covered in T03-T04)
- Integration tests with real database
- Performance optimization beyond basic indexing (already exists)

## Dependencies
- Depends on: none (uses existing Chunk model and database schema)
- Unblocks: T02 (API endpoints need these core functions)

## Implementation plan
1. Create new file `src/vulcanlab/data/chunk_operations.py`
2. Import required dependencies: SQLAlchemy Session, Chunk model, typing annotations
3. Implement `search_chunks_lexical()`:
   - Accept query, page, page_size, session parameters
   - Extract last heading from `heading_breadcrumbs` using split on " > " and take last element
   - Handle None breadcrumbs gracefully (treat as no title match)
   - Use SQLAlchemy case expressions to rank results:
     - Priority 1: Exact title match (extracted heading equals query, case-insensitive)
     - Priority 2: Partial title match (extracted heading contains query, case-insensitive)
     - Priority 3: Content match (content contains query, case-insensitive)
   - Use ILIKE for case-insensitive matching
   - Apply pagination with LIMIT and OFFSET
   - Return tuple of (results list, total count)
   - Use separate count query for total_results
4. Implement `get_all_descendants()`:
   - Query chunks where parent_id equals given chunk_id
   - For each child, recursively call get_all_descendants()
   - Collect all descendants in flat list
   - Return list of Chunk objects (not just IDs)
   - Handle non-existent chunk_id by returning empty list (not an error for this function)
5. Implement `delete_chunk_cascade()`:
   - Verify chunk exists, raise ValueError if not found
   - Get all descendants first (for logging count)
   - Delete the chunk using session.delete()
   - Database CASCADE will automatically handle descendants via FK constraint
   - Commit is handled by caller (session management pattern)
   - Return total count (1 + len(descendants))
   - Log INFO message with chunk_id and descendant count before deletion
6. Add proper docstrings with type hints for all functions
7. Add logging statements (INFO for deletions, ERROR for failures)

- Patterns to apply:
  - **Session management pattern**: All functions accept session as parameter, never create sessions internally
  - **Core module independence**: No FastAPI or HTTP imports, pure Python with SQLAlchemy
  - **Database patterns**: Use SQLAlchemy ORM queries, rely on existing CASCADE FK constraint
  - **Error handling**: Raise specific exceptions (ValueError), let caller handle transactions

- Deviations (if any):
  - None: Fully aligned with patterns.md

## Unit tests (required)
- Add tests for:
  - **test_search_chunks_lexical_exact_title_match**: Create chunk with heading_breadcrumbs="Chapter 1 > Introduction", search "Introduction", verify it appears first
  - **test_search_chunks_lexical_partial_title_match**: Create chunks with partial title matches, verify ordering after exact matches
  - **test_search_chunks_lexical_content_match**: Create chunks with query in content but not title, verify they appear after title matches
  - **test_search_chunks_lexical_combined_ranking**: Create mix of exact title, partial title, and content matches, verify correct ordering
  - **test_search_chunks_lexical_no_breadcrumbs**: Create chunk with None heading_breadcrumbs, verify no crash and falls to content search
  - **test_search_chunks_lexical_pagination**: Create 50 chunks, verify page 1 has 25, page 2 has 25, total_count is 50
  - **test_search_chunks_lexical_empty_results**: Search for non-existent term, verify empty list and count 0
  - **test_search_chunks_lexical_case_insensitive**: Search "reference" and verify matches "Reference" in title
  - **test_get_all_descendants_multi_level**: Create parent->child->grandchild->great-grandchild, verify all 3 descendants returned
  - **test_get_all_descendants_single_level**: Create parent with 2 children (no grandchildren), verify 2 descendants returned
  - **test_get_all_descendants_no_children**: Call on leaf node, verify empty list returned
  - **test_get_all_descendants_non_existent_chunk**: Call with invalid chunk_id, verify empty list (not error)
  - **test_delete_chunk_cascade_multi_level**: Create 4-level tree, delete parent, verify all descendants deleted
  - **test_delete_chunk_cascade_leaf_node**: Delete chunk with no children, verify count=1 returned
  - **test_delete_chunk_cascade_returns_correct_count**: Create parent with 5 total descendants, verify count=6 returned
  - **test_delete_chunk_cascade_non_existent_chunk**: Call with invalid chunk_id, verify ValueError raised
  - **test_delete_chunk_cascade_orphan_prevention**: Create tree, delete parent, query database to verify no orphaned children remain
  - **test_title_extraction_multiple_levels**: Verify "H1 > H2 > H3" extracts "H3" correctly
  - **test_title_extraction_single_level**: Verify "H1" extracts "H1" correctly
  - **test_title_extraction_empty_breadcrumbs**: Verify None or empty string handled gracefully

- Suggested locations:
  - `tests/unit/test_chunk_operations.py` (new file)

- Mocking/fakes needed:
  - Mock SQLAlchemy session using unittest.mock or pytest fixtures
  - Create in-memory test Chunk objects (do not connect to real database)
  - Mock session.query() to return test data
  - Mock session.delete() to track calls without actual deletion
  - For orphan prevention test, track session.query() calls to verify no orphaned parent_ids remain

## Acceptance criteria (checklist)
- [ ] File `src/vulcanlab/data/chunk_operations.py` created with all three functions
- [ ] `search_chunks_lexical()` extracts last heading from breadcrumbs correctly
- [ ] `search_chunks_lexical()` ranks exact title matches first, then partial, then content
- [ ] `search_chunks_lexical()` handles None breadcrumbs without crashing
- [ ] `search_chunks_lexical()` paginates correctly with LIMIT/OFFSET
- [ ] `get_all_descendants()` recursively retrieves all descendants at any depth
- [ ] `get_all_descendants()` returns empty list for leaf nodes and non-existent IDs
- [ ] `delete_chunk_cascade()` raises ValueError for non-existent chunk_id
- [ ] `delete_chunk_cascade()` returns correct count including the parent chunk
- [ ] All functions accept session parameter and never create sessions internally
- [ ] All functions have proper docstrings with type hints
- [ ] Logging statements added for deletions (INFO level with chunk_id and count)
- [ ] All 20+ unit tests pass with 100% coverage of new code
- [ ] Unit tests verify no orphaned chunks after cascading deletion

## Manual verification
- Steps:
  1. Run pytest on `tests/unit/test_chunk_operations.py`
  2. Verify all tests pass
  3. Check code coverage report shows 100% coverage for chunk_operations.py
  4. Review test output for proper logging messages during deletion tests

- Expected results:
  - All unit tests pass
  - No integration with real database needed (all mocked)
  - Code coverage at 100% for new module
  - Functions are ready to be called by API layer in T02

## Notes
- The CASCADE deletion behavior already exists in the Chunk model schema: `ForeignKey("chunks.id", ondelete="CASCADE")`
- This means when we delete a parent chunk, PostgreSQL automatically deletes all children
- The `get_all_descendants()` function is needed for preview (showing user what will be deleted) before deletion
- Title extraction logic: `heading_breadcrumbs.split(" > ")[-1] if heading_breadcrumbs else None`
- For ranking, use SQLAlchemy `case()` expression to assign priority values, then order by priority
- Pagination: offset = (page - 1) * page_size, limit = page_size
- Recursive descendant retrieval can be optimized with PostgreSQL CTE later if needed, but iterative approach is simpler initially
- Session commit is handled by the API layer (caller), not by these core functions
- All database operations should use parameterized queries (SQLAlchemy ORM handles this automatically)
