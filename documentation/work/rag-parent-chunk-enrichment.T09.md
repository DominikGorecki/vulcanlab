# Ticket: rag-parent-chunk-enrichment.T09 - Observability and Logging

## Source
- Spec: documentation/work/rag-parent-chunk-enrichment.spec.md
- Patterns: documentation/patterns.md

## Goal
- Add structured logging for parent traversal and enrichment operations
- Track metrics for monitoring RAG quality improvements
- Enable debugging and troubleshooting of enrichment behavior

## Scope
### In scope
- Log when parent traversal reaches root without meeting `min_word_count`
- Log when chunks are filtered out due to inability to enrich
- Track and log average parent depth traversed per query
- Track and log percentage of chunks enriched per query
- Log coverage calculations and parent replacement decisions
- Add debug-level logging for detailed enrichment steps
- Ensure logs follow project logging patterns

### Out of scope
- Metrics dashboards or visualization
- APM integration (Datadog, New Relic, etc.)
- Performance profiling
- User-facing metrics display

## Dependencies
- Depends on: T07 (End-to-end Integration)
- Unblocks: T12 (Manual Testing)

## Implementation plan
1. Review existing logging patterns in `src/vulcanlab/retrieval/` and `src/vulcanlab/augmentation/`
2. Import logging module and set up logger in relevant modules
3. Add logging to `enrich_chunk_from_parent()`:
   - INFO: Log when traversal completes (depth, final parent word_count)
   - WARNING: Log when traversal reaches root without meeting min_word_count
   - DEBUG: Log each parent step in traversal (chunk_id, parent_id, word_count)
4. Add logging to retrieval enrichment integration:
   - INFO: Log enrichment summary per query (total chunks, enriched count, average depth)
   - DEBUG: Log each chunk enrichment decision (enriched or not, reason)
5. Add logging to consolidation:
   - INFO: Log coverage calculations (parent_id, coverage percentage, replacement decision)
   - DEBUG: Log adjacency merging operations (chunk IDs, line ranges extracted)
6. Track metrics during query execution:
   - Count total chunks retrieved
   - Count chunks enriched
   - Sum traversal depths and calculate average
   - Calculate enrichment percentage
7. Format logs for structured logging (JSON if project uses it):
   - Include relevant context: query_id, chunk_id, parent_id, word_count, depth
8. Add log level configuration:
   - Ensure INFO level provides useful operational insights
   - Ensure DEBUG level provides detailed troubleshooting info
   - Avoid WARN/ERROR unless actual problems occur

Patterns to apply:
- Core Module Independence - Use standard Python logging, no framework-specific loggers
- Observability - Structured logging with context

Deviations (if any):
- None

## Unit tests (required)
- Add tests for:
  - Logger called when parent traversal reaches root
  - Logger called when chunk filtered due to enrichment failure
  - Enrichment metrics calculated correctly (average depth, percentage enriched)
  - Coverage calculation logged with correct values
  - Parent replacement decision logged
  - Log messages contain expected context (chunk_id, parent_id, etc.)
  - Log levels used appropriately (INFO for summaries, DEBUG for details)

- Suggested locations:
  - `tests/unit/test_enrichment_logging.py`
  - Add logging assertions to existing tests (test_enrich_from_parent.py, test_consolidate_parent_chunks.py)

- Mocking/fakes needed:
  - Mock logger or use caplog pytest fixture
  - Capture log output for assertion

## Acceptance criteria (checklist)
- [ ] Logging added to `enrich_chunk_from_parent()` function
- [ ] Warning logged when traversal reaches root without meeting min_word_count
- [ ] Info logged when chunks filtered out due to enrichment issues
- [ ] Average parent depth tracked and logged per query
- [ ] Percentage of chunks enriched tracked and logged per query
- [ ] Coverage calculation logged in consolidation
- [ ] Parent replacement decisions logged
- [ ] Debug-level logging available for detailed troubleshooting
- [ ] Log messages include relevant context (IDs, counts, percentages)
- [ ] Logs follow project logging patterns
- [ ] All unit tests pass

## Manual verification
- Steps:
  1. Run retrieval query with various chunk sizes
  2. Check logs for enrichment summary (INFO level)
  3. Enable DEBUG logging
  4. Run retrieval query again
  5. Verify detailed step-by-step enrichment logs appear
  6. Run consolidation with various coverage scenarios
  7. Check logs for coverage calculations and replacement decisions
  8. Verify log format is consistent and parseable

- Expected results:
  - INFO logs show high-level enrichment metrics
  - DEBUG logs show detailed traversal steps
  - Warnings appear when traversal reaches root without meeting minimum
  - Coverage calculations visible in consolidation logs
  - Log output is clear and useful for debugging

## Notes
- Example log messages:
  - INFO: `Enrichment summary: 17 chunks, 12 enriched (70.6%), avg depth 1.8`
  - WARNING: `Chunk 12345 traversal reached root (depth 3) without meeting min_word_count (150), using topmost parent (word_count: 95)`
  - DEBUG: `Enriching chunk 12345: traversed to parent 12300 (depth 1, word_count 180), within max, using full parent`
  - INFO: `Consolidation group parent_id=12300: coverage 0.65 (65%), threshold 0.5, replacing with parent`
- Use Python's standard logging module:
  ```python
  import logging
  logger = logging.getLogger(__name__)

  logger.info(f"Enrichment summary: {total} chunks, {enriched} enriched ({pct:.1f}%), avg depth {avg_depth:.1f}")
  logger.warning(f"Chunk {chunk_id} traversal reached root without meeting min_word_count")
  logger.debug(f"Traversing chunk {chunk_id} to parent {parent_id} (depth {depth}, word_count {wc})")
  ```
- If project uses structured logging (e.g., structlog), adapt format accordingly
- Include query_id or session_id if available for tracing
- Metrics to track:
  - `total_chunks_retrieved` (int)
  - `chunks_enriched` (int)
  - `enrichment_percentage` (float)
  - `average_traversal_depth` (float)
  - `traversal_reached_root_count` (int)
  - `parent_replacements` (int)
  - `coverage_calculations` (list of floats)
- Consider adding metrics to return value of retrieval function for observability
