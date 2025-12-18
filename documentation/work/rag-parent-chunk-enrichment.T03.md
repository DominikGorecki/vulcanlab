# Ticket: rag-parent-chunk-enrichment.T03 - Consolidation Refactor Using Parent Chunks

## Source
- Spec: documentation/work/rag-parent-chunk-enrichment.spec.md
- Patterns: documentation/patterns.md

## Goal
- Refactor consolidation logic to use parent chunk content instead of local markdown files
- Implement character-count-based coverage calculation for parent replacement
- Enable consolidation to work for all document types (including Simple Conversion)

## Scope
### In scope
- Update adjacency merging in `src/vulcanlab/augmentation/consolidate_context.py`
- Replace file reads with parent chunk content extraction
- Implement character-count coverage calculation for parent-level replacement
- Use `start_line` and `end_line` to extract content ranges from parent chunks
- Preserve heading chains (breadcrumbs) in consolidated output
- Unit tests with mocked chunk data

### Out of scope
- Retrieval enrichment (T02)
- Migration or config changes (T04, T05)
- UI changes (T06)
- Consolidation grouping logic changes (still by work_id and parent_id)

## Dependencies
- Depends on: T02 (Parent Traversal Enrichment)
- Unblocks: T07 (End-to-end Integration)

## Implementation plan
1. Read existing consolidation logic in `src/vulcanlab/augmentation/consolidate_context.py`
2. Locate adjacency merging logic (fills gaps between adjacent chunks in same parent group)
3. Replace local markdown file reading with parent chunk content extraction:
   - Query parent chunk by parent_id
   - Use parent.content to get full text
   - Extract lines between child chunks using start_line and end_line
   - Build merged content string
4. Update parent-level replacement logic:
   - For each parent group, calculate coverage: `sum(len(child.content) for child in group) / len(parent.content)`
   - If coverage > coverage_threshold, replace entire group with parent chunk content
   - Include parent title in replacement
5. Ensure heading chain preservation:
   - For content chunks: use heading_breadcrumbs
   - For heading chunks: extract from first line of content
   - Prepend breadcrumbs to consolidated output
6. Handle edge cases:
   - Parent chunk missing: skip merging, return children as-is
   - Parent content empty: skip merging
   - start_line or end_line out of bounds: clamp to content boundaries
7. Write comprehensive unit tests

Patterns to apply:
- Core Module Independence - No FastAPI imports
- Session Management - Database session passed explicitly
- ORM - Query parent chunks via SQLAlchemy

Deviations (if any):
- None

## Unit tests (required)
- Add tests for:
  - Adjacency merging extracts correct content range from parent using start_line/end_line
  - Merged content includes gap between adjacent chunks
  - Parent-level replacement triggered when coverage exceeds threshold
  - Parent-level replacement not triggered when coverage below threshold
  - Coverage calculation uses character counts (len of content strings)
  - Heading chain preserved in merged output (from heading_breadcrumbs)
  - Heading chain preserved for heading chunks (from first line)
  - Groups with same parent_id processed correctly
  - Missing parent chunk handled gracefully (return original chunks)
  - Out-of-bounds start_line/end_line clamped correctly
  - Empty parent content handled (skip merging)

- Suggested locations:
  - `tests/unit/test_consolidate_parent_chunks.py`

- Mocking/fakes needed:
  - Mock SQLAlchemy Session
  - Mock Chunk model instances with parent relationships
  - Mock parent chunk content with known line counts

## Acceptance criteria (checklist)
- [ ] Adjacency merging refactored to use parent chunk content
- [ ] Local markdown file reads removed from consolidation
- [ ] start_line and end_line used to extract content ranges
- [ ] Character-count-based coverage calculation implemented
- [ ] Parent replacement triggered correctly when coverage > threshold
- [ ] Heading chains preserved in all consolidated outputs
- [ ] Edge cases handled (missing parent, empty content, bounds checking)
- [ ] Consolidation works for Simple Conversion documents (no local files)
- [ ] All unit tests pass
- [ ] Code follows snake_case naming convention

## Manual verification
- Steps:
  1. Run unit tests: `python -m pytest tests/unit/test_consolidate_parent_chunks.py -v`
  2. Create test chunks with known parent relationships and content
  3. Run consolidation with various coverage_threshold values
  4. Verify parent replacement occurs when expected
  5. Verify merged content includes correct line ranges
  6. Test with Simple Conversion document (database-only content)

- Expected results:
  - Unit tests pass
  - Adjacency merging uses parent content correctly
  - Parent replacement triggered at appropriate coverage levels
  - No errors when local markdown files don't exist
  - Consolidated output maintains heading context

## Notes
- Consolidation grouping by work_id and parent_id remains unchanged (spec non-goal)
- Character count calculation: use `len(chunk.content)` for each chunk
- Coverage formula: `sum(len(child.content) for child in group) / len(parent.content)`
- coverage_threshold default is 0.5 (50%)
- Line extraction from parent content: `parent_lines = parent.content.split('\n'); extracted = '\n'.join(parent_lines[start_line:end_line])`
- heading_breadcrumbs format: JSON array, join with " > " for display
- For heading chunks, first line typically contains the heading itself
- Ensure merged content doesn't duplicate headings already in breadcrumbs
- This completes the core database-driven enrichment (no more file dependencies)
