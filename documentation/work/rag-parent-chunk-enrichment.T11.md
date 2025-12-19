# Ticket: rag-parent-chunk-enrichment.T11 - Performance Optimization

## Source
- Spec: documentation/work/rag-parent-chunk-enrichment.spec.md
- Patterns: documentation/patterns.md

## Goal
- Optimize parent traversal to avoid N+1 query problems
- Ensure enrichment process meets performance target (<10% latency increase)
- Use efficient database queries (joins, recursive CTEs) where appropriate
- Minimize overhead from sentence tokenization and content processing

## Scope
### In scope
- Database query optimization for parent traversal
- Use of recursive CTEs or eager loading for parent chains
- Batch processing where applicable
- Lightweight sentence boundary detection
- Performance testing and benchmarking
- Unit tests for optimized code paths

### Out of scope
- Caching layers (Redis, etc.)
- Database indexing changes (assume indexes on parent_id exist)
- Async/parallel processing
- Performance monitoring infrastructure
- Load testing or stress testing

## Dependencies
- Depends on: T07 (End-to-end Integration), T10 (Edge Cases)
- Unblocks: T12 (Manual Testing)

## Implementation plan
1. Review current parent traversal implementation from T02
2. Analyze potential N+1 query issues:
   - Current approach: Iterative queries for each parent_id
   - Problem: For 17 chunks with depth 2, could be 34 queries
3. Implement optimized parent traversal using recursive CTE:
   - Create SQL query that fetches entire parent chain in one database round-trip
   - Use PostgreSQL recursive CTE to walk parent_id relationships
   - Filter for first parent meeting min_word_count
   - Return full chain for use in truncation if needed
4. Alternative: Use eager loading with SQLAlchemy:
   - Define parent relationship on Chunk model if not already defined
   - Use `selectinload()` or `joinedload()` to fetch parents eagerly
   - Evaluate which approach is more efficient
5. Optimize sentence tokenization:
   - Benchmark spaCy vs regex approaches
   - If spaCy too slow, use regex as primary (not fallback)
   - Consider sentence boundary detection only when truncation needed
6. Optimize word counting:
   - Use cached word_count from database instead of recalculating
   - Only count words on truncated content if necessary
7. Batch operations where possible:
   - If multiple chunks share same parent, query parent once
   - Cache parent chunks in dict during single retrieval pass
8. Add performance benchmarks:
   - Measure retrieval latency before and after enrichment
   - Target: <10% increase for typical queries (17-75 chunks)
   - Measure database query count
9. Write unit tests for optimized code

Patterns to apply:
- ORM - Use SQLAlchemy relationships and eager loading
- Database - Use recursive CTEs for hierarchical queries
- Performance - Minimize database round-trips

Deviations (if any):
- None

## Unit tests (required)
- Add tests for:
  - Recursive CTE query returns full parent chain
  - Recursive CTE query stops at first parent meeting min_word_count
  - Eager loading fetches parents without N+1 queries
  - Parent chunk caching prevents duplicate queries
  - Sentence tokenization only runs when truncation needed
  - Word counting uses database values when available
  - Optimized path produces same results as naive implementation
  - Performance benchmark shows <10% latency increase
  - Database query count reduced vs naive approach

- Suggested locations:
  - `tests/unit/test_enrichment_performance.py`

- Mocking/fakes needed:
  - Mock SQLAlchemy Session with query counting
  - Mock Chunk models with parent relationships
  - Timing utilities for benchmarks

## Acceptance criteria (checklist)
- [ ] Recursive CTE or eager loading implemented for parent traversal
- [ ] N+1 query problem eliminated
- [ ] Parent chunk caching implemented for shared parents
- [ ] Sentence tokenization optimized (lazy evaluation)
- [ ] Word counting uses database values
- [ ] Performance benchmark shows <10% latency increase
- [ ] Database query count significantly reduced
- [ ] Optimized code produces identical results to naive implementation
- [ ] All unit tests pass
- [ ] Code follows snake_case naming convention

## Manual verification
- Steps:
  1. Run performance benchmark tests
  2. Enable query logging in PostgreSQL or SQLAlchemy
  3. Run retrieval with 17 chunks (typical query)
  4. Count total database queries
  5. Measure total retrieval latency
  6. Compare to baseline (retrieval without enrichment)
  7. Verify <10% increase
  8. Test with 75 chunks (max after RRF)
  9. Verify performance scales acceptably

- Expected results:
  - Query count much lower than naive approach
  - Latency increase <10% for typical queries
  - No performance regression for edge cases
  - Enrichment overhead barely noticeable

## Notes
- Recursive CTE example for PostgreSQL:
  ```sql
  WITH RECURSIVE parent_chain AS (
    -- Base case: start with the chunk
    SELECT id, parent_id, content, word_count, heading_breadcrumbs, 0 AS depth
    FROM chunks
    WHERE id = :chunk_id

    UNION ALL

    -- Recursive case: fetch parents
    SELECT c.id, c.parent_id, c.content, c.word_count, c.heading_breadcrumbs, pc.depth + 1
    FROM chunks c
    INNER JOIN parent_chain pc ON c.id = pc.parent_id
    WHERE pc.parent_id IS NOT NULL AND pc.depth < 10
  )
  SELECT * FROM parent_chain
  WHERE word_count >= :min_word_count
  ORDER BY depth ASC
  LIMIT 1;
  ```
- SQLAlchemy eager loading example:
  ```python
  from sqlalchemy.orm import selectinload

  chunk = session.query(Chunk).options(
      selectinload(Chunk.parent)
  ).filter_by(id=chunk_id).first()
  ```
- Parent caching during retrieval:
  ```python
  parent_cache = {}
  for chunk in chunks:
      if chunk.parent_id not in parent_cache:
          parent_cache[chunk.parent_id] = session.query(Chunk).get(chunk.parent_id)
      parent = parent_cache[chunk.parent_id]
      # ... enrichment logic
  ```
- Performance target: <10% increase
  - Baseline (no enrichment): e.g., 150ms
  - With enrichment: <165ms
- Assume indexes exist on chunks.parent_id (standard foreign key index)
- Benchmark methodology:
  - Run 10 queries, take median latency
  - Use realistic chunk counts (17-75)
  - Measure end-to-end retrieval time
  - Measure database query count separately
- If spaCy is too slow (>50ms for typical content), use regex as primary
- Consider lazy sentence tokenization: only tokenize if truncation needed
