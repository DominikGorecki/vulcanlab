# Ticket: rag-parent-chunk-enrichment.T10 - Edge Case Handling and Fallbacks

## Source
- Spec: documentation/work/rag-parent-chunk-enrichment.spec.md
- Patterns: documentation/patterns.md

## Goal
- Implement robust error handling for edge cases in parent traversal and consolidation
- Ensure system degrades gracefully when encountering malformed data
- Prevent pipeline failures due to missing or corrupted chunk relationships

## Scope
### In scope
- Handle missing parent chunks (deleted, not found in database)
- Handle orphaned chunks (parent_id is None or invalid)
- Handle circular parent references (A -> B -> C -> A)
- Handle malformed chunk data (missing attributes, null content)
- Handle out-of-bounds line ranges in consolidation
- Handle empty parent content
- Implement fallback to original chunk when enrichment impossible
- Add comprehensive unit tests for all edge cases

### Out of scope
- Data repair or migration (fixing malformed data)
- Schema changes to prevent malformed data
- Performance optimization
- User-facing error messages (beyond logging)

## Dependencies
- Depends on: T07 (End-to-end Integration)
- Unblocks: T11 (Performance Optimization), T12 (Manual Testing)

## Implementation plan
1. Review current edge case handling in T02 and T03 implementations
2. Enhance `enrich_chunk_from_parent()` with additional safeguards:
   - Check if parent_id is None: return original chunk immediately
   - Check if parent chunk query returns None: return original chunk
   - Track visited parent IDs in set to detect circular references
   - Limit traversal depth to 10 (or configurable max)
   - Check if parent.content is None or empty: return original chunk
   - Check if parent.word_count is None: calculate on the fly or return original
3. Enhance consolidation edge case handling:
   - Check if parent chunk missing: skip merging, return child chunks as-is
   - Check if parent.content is None or empty: skip merging
   - Clamp start_line and end_line to actual content bounds:
     ```python
     lines = parent.content.split('\n')
     start = max(0, min(start_line, len(lines)))
     end = max(0, min(end_line, len(lines)))
     ```
   - Handle case where start_line > end_line: log warning, return empty or original
   - Handle case where coverage calculation divides by zero (empty parent): skip replacement
4. Add defensive checks for chunk attributes:
   - Ensure chunk.content is not None before processing
   - Ensure chunk.word_count is valid (>= 0)
   - Ensure chunk.parent_id is valid type (int or None)
5. Implement fallback strategy:
   - Always prefer returning original chunk over raising exception
   - Log warnings for all fallback scenarios
   - Track fallback count for observability
6. Write comprehensive unit tests for each edge case

Patterns to apply:
- Core Module Independence - No framework-specific error handling
- Error Handling - Graceful degradation, log and continue
- Defensive Programming - Validate inputs, check assumptions

Deviations (if any):
- None

## Unit tests (required)
- Add tests for:
  - Orphaned chunk (parent_id is None) returns original chunk
  - Missing parent chunk (query returns None) returns original chunk
  - Circular reference detected (A -> B -> C -> A) stops traversal
  - Max depth limit prevents infinite recursion
  - Empty parent content returns original chunk
  - Null parent content returns original chunk
  - Missing word_count attribute handled gracefully
  - Out-of-bounds start_line clamped to content length
  - Out-of-bounds end_line clamped to content length
  - start_line > end_line handled gracefully
  - Division by zero in coverage calculation prevented
  - Malformed heading_breadcrumbs handled (not valid JSON)
  - Null chunk.content handled gracefully
  - Invalid parent_id type handled (e.g., string instead of int)
  - Fallback warnings logged correctly

- Suggested locations:
  - `tests/unit/test_enrichment_edge_cases.py`
  - `tests/unit/test_consolidation_edge_cases.py`

- Mocking/fakes needed:
  - Mock SQLAlchemy Session returning None for missing parents
  - Mock Chunk instances with malformed data
  - Mock circular parent relationships

## Acceptance criteria (checklist)
- [ ] Missing parent chunks handled gracefully (return original chunk)
- [ ] Orphaned chunks handled gracefully (return original chunk)
- [ ] Circular references detected and prevented
- [ ] Max traversal depth enforced (default 10)
- [ ] Empty or null parent content handled gracefully
- [ ] Out-of-bounds line ranges clamped correctly
- [ ] Division by zero in coverage prevented
- [ ] Malformed chunk data handled without exceptions
- [ ] Fallback to original chunk implemented for all failure scenarios
- [ ] Warnings logged for all edge cases
- [ ] Pipeline continues despite individual chunk failures
- [ ] All unit tests pass

## Manual verification
- Steps:
  1. Run edge case unit tests: `python -m pytest tests/unit/test_enrichment_edge_cases.py -v`
  2. Create test chunks with missing parents in database
  3. Run retrieval and verify no crashes
  4. Create circular parent references in test data
  5. Run enrichment and verify traversal stops
  6. Test with malformed chunk data (null content, missing attributes)
  7. Verify warnings appear in logs
  8. Verify original chunks returned in all fallback scenarios

- Expected results:
  - No exceptions raised during edge case scenarios
  - Original chunks returned when enrichment impossible
  - Warnings logged for all edge cases
  - Pipeline completes successfully despite bad data
  - Fallback count tracked in observability metrics

## Notes
- Fallback philosophy: "Always return something usable, never crash"
- Edge case priority:
  1. Missing parent (most common)
  2. Circular references (rare but critical)
  3. Malformed data (varies by data quality)
- Circular reference detection:
  ```python
  def enrich_chunk_from_parent(...):
      visited = set()
      current = chunk
      depth = 0

      while current.parent_id and depth < 10:
          if current.parent_id in visited:
              logger.warning(f"Circular reference detected at chunk {current.id}")
              return original_chunk_dict

          visited.add(current.id)
          current = session.query(Chunk).get(current.parent_id)
          if not current:
              logger.warning(f"Parent {parent_id} not found")
              return original_chunk_dict

          depth += 1
          # ... rest of logic
  ```
- Line range clamping:
  ```python
  lines = parent.content.split('\n')
  start = max(0, min(start_line, len(lines)))
  end = max(start, min(end_line, len(lines)))  # Ensure end >= start
  extracted = '\n'.join(lines[start:end])
  ```
- Coverage division by zero check:
  ```python
  if len(parent.content) == 0:
      logger.warning(f"Parent {parent_id} has empty content, skipping replacement")
      # Don't calculate coverage, don't replace
  else:
      coverage = sum(len(c.content) for c in children) / len(parent.content)
  ```
- Track fallback counts in metrics dict for observability
- Consider adding health check endpoint that reports recent fallback rates
