# Ticket: rag-parent-chunk-enrichment.T02 - Parent Traversal Enrichment (Core Vertical Slice)

## Source
- Spec: documentation/work/rag-parent-chunk-enrichment.spec.md
- Patterns: documentation/patterns.md

## Goal
- Implement parent-chunk traversal algorithm for retrieval enrichment
- Replace local markdown file dependency with database-driven parent content
- Deliver first vertical slice: improved context quality for short chunks

## Scope
### In scope
- `enrich_chunk_from_parent()` function in `src/vulcanlab/retrieval/retrieve.py`
- Parent hierarchy traversal using `parent_id` chain
- Title extraction from `heading_breadcrumbs` (content chunks) or first line (heading chunks)
- Integration with existing retrieval pipeline (post-RRF, pre-reranking)
- Unit tests with mocked database session
- Functional improvement visible in retrieval results

### Out of scope
- Consolidation changes (T03)
- Migration or config changes (T04, T05)
- UI changes (T06)
- Observability/logging enhancements (T09)

## Dependencies
- Depends on: T01 (Core Helper Functions)
- Unblocks: T03 (Consolidation Refactor)

## Implementation plan
1. Read existing retrieval logic in `src/vulcanlab/retrieval/retrieve.py`
2. Implement `enrich_chunk_from_parent(chunk, session, min_word_count, max_word_count) -> dict`:
   - Query chunk.parent_id recursively until parent.word_count >= min_word_count
   - Track traversal depth for logging
   - If parent found and word_count <= max_word_count: use full parent content
   - If parent found and word_count > max_word_count: call `truncate_to_word_limit()` from T01
   - If no parent meets minimum (reached root): return topmost parent reached
   - Extract title from parent chunk (heading_breadcrumbs or first line of content)
   - Return dict with keys: 'content', 'title', 'parent_id', 'enriched', 'depth'
3. Implement `extract_chunk_title(chunk) -> str` helper:
   - For content chunks: parse heading_breadcrumbs (JSON array of headings)
   - For heading chunks: use first line of content
4. Integrate enrichment into existing retrieval flow:
   - Locate post-RRF shortlist generation (before reranking)
   - For each chunk in shortlist, check if word_count < min_word_count
   - If true, call `enrich_chunk_from_parent()`
   - Replace chunk content with enriched content
5. Handle edge cases:
   - Missing parent_id (orphaned chunk): use original chunk
   - Null parent chunk (deleted or missing): use original chunk
   - Circular parent references: limit traversal depth to 10
6. Write comprehensive unit tests

Patterns to apply:
- Core Module Independence - No FastAPI imports, operates on SQLAlchemy models
- Session Management - Database session passed as explicit argument
- ORM - Use SQLAlchemy relationships or query by parent_id

Deviations (if any):
- None

## Unit tests (required)
- Add tests for:
  - Parent traversal stops at first parent meeting min_word_count
  - Parent traversal reaches root when no parent meets minimum
  - Full parent content used when word_count <= max_word_count
  - Sliding window truncation applied when word_count > max_word_count
  - Title extraction from heading_breadcrumbs for content chunks
  - Title extraction from first line for heading chunks
  - Orphaned chunk (parent_id is None) returns original chunk
  - Missing parent chunk returns original chunk
  - Circular reference protection (max depth 10)
  - Enriched flag set correctly in return dict
  - Traversal depth tracked accurately

- Suggested locations:
  - `tests/unit/test_enrich_from_parent.py`

- Mocking/fakes needed:
  - Mock SQLAlchemy Session
  - Mock Chunk model instances with parent relationships
  - Mock database queries for parent_id lookups

## Acceptance criteria (checklist)
- [ ] `enrich_chunk_from_parent()` implemented in `src/vulcanlab/retrieval/retrieve.py`
- [ ] `extract_chunk_title()` helper implemented
- [ ] Parent traversal walks up parent_id chain correctly
- [ ] Traversal stops at first parent meeting min_word_count
- [ ] Traversal reaches root if no parent meets minimum
- [ ] Full parent content used when within max_word_count
- [ ] Truncation applied when parent exceeds max_word_count
- [ ] Title correctly extracted from both chunk types
- [ ] Edge cases handled (orphaned chunks, missing parents, circular refs)
- [ ] Enrichment integrated into retrieval pipeline
- [ ] All unit tests pass
- [ ] Code follows snake_case naming convention

## Manual verification
- Steps:
  1. Run unit tests: `python -m pytest tests/unit/test_enrich_from_parent.py -v`
  2. Query database for a short chunk (< min_word_count) with parent hierarchy
  3. Run retrieval with test query that returns short chunks
  4. Inspect enriched chunks in debug output
  5. Verify parent content is included and properly titled

- Expected results:
  - Unit tests pass
  - Short chunks are enriched with parent content
  - Enriched chunks include hierarchical context
  - Retrieval quality visibly improved for short fragments

## Notes
- Use recursive query or iterative parent_id traversal (prefer iterative for simplicity)
- Example SQLAlchemy query: `session.query(Chunk).filter_by(id=parent_id).first()`
- Chunk model likely has attributes: id, parent_id, word_count, content, heading_breadcrumbs, start_line, end_line
- heading_breadcrumbs format: JSON array like `["Chapter 1", "Section 1.1", "Subsection"]`
- For heading chunks, content typically starts with the heading itself (e.g., "## Introduction")
- Circular reference protection: track visited chunk IDs in a set during traversal
- Max traversal depth of 10 prevents infinite loops and excessive DB queries
- This is the first vertical slice: enables manual testing of improved retrieval context
