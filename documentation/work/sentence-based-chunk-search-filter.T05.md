# Ticket: sentence-based-chunk-search-filter.T05 - Create Backfill Migration for Existing Chunks

## Source
- Spec: documentation/work/sentence-based-chunk-search-filter.spec.md
- Patterns: documentation/patterns.md

## Goal
- Create Python migration script to populate sentence_count for existing chunks
- Process chunks in batches with progress logging
- Make migration idempotent and safe to re-run

## Scope
### In scope
- Create migrations/019_backfill_sentence_count.py with upgrade/downgrade functions
- Create migrations/019_run_migration.py runner script
- Read sanitized_markdown for each work, re-parse to extract chunk content
- Count sentences using same _get_sentences() logic from content_chunking
- Update chunks.sentence_count in batches (50-100 chunks per transaction)
- Log progress every 100 chunks
- Handle errors gracefully: log warning, set sentence_count=NULL, continue

### Out of scope
- UI for monitoring progress
- Real-time progress updates
- Modifying chunks that already have sentence_count set (skip them for idempotency)

## Dependencies
- Depends on: T01 (column exists), T02 (sentence counting logic exists)
- Unblocks: Production rollout

## Implementation plan
- Create migrations/019_backfill_sentence_count.py following pattern from 010_refactor_heading_breadcrumbs.py
- Implement upgrade(connection) function:
  - Query all chunks WHERE sentence_count IS NULL AND level='chunk'
  - Group by work_id to process work by work
  - For each work: fetch sanitized_markdown content
  - Re-parse markdown to identify chunk boundaries (reuse logic or import from content_chunking)
  - For each chunk, count sentences using _get_sentences()
  - Batch UPDATE chunks SET sentence_count=X WHERE id IN (...)
  - Commit every 50-100 chunks
  - Log progress every 100 chunks: "Processed 500/5000 chunks"
  - Handle errors: try/except around sentence counting, set NULL on error, log warning
- Implement downgrade(connection) function:
  - UPDATE chunks SET sentence_count=NULL (rollback)
- Create migrations/019_run_migration.py runner following pattern from 010_run_migration.py
  - Import upgrade/downgrade functions
  - Handle --downgrade flag
  - Print status and results
- Patterns to apply:
  - SQL migrations: Data backfill in .py script
  - Idempotency: Only process chunks WHERE sentence_count IS NULL
  - Batch processing: Commit every N chunks to avoid memory issues
- Deviations (if any):
  - None

## Unit tests (required)
- Add tests for:
  - upgrade() function processes only chunks with sentence_count=NULL
  - upgrade() skips chunks that already have sentence_count set
  - upgrade() updates sentence_count correctly for level='chunk' chunks
  - upgrade() does NOT update non-chunk levels (H1-H5)
  - Error during sentence counting sets sentence_count=NULL and continues
  - Batch processing commits every N chunks (verify transaction handling)
  - Progress logging occurs every 100 chunks (mock logger)
  - downgrade() sets sentence_count=NULL for all chunks
- Suggested locations:
  - tests/unit/test_migration_019.py
- Mocking/fakes needed:
  - Mock database connection and queries
  - Mock _get_sentences for controlled test cases
  - Mock sanitized_markdown content

## Acceptance criteria (checklist)
- [ ] migrations/019_backfill_sentence_count.py created with upgrade/downgrade
- [ ] migrations/019_run_migration.py runner script created
- [ ] Migration processes only chunks with sentence_count=NULL (idempotent)
- [ ] Batch processing commits every 50-100 chunks
- [ ] Progress logging every 100 chunks
- [ ] Errors logged as warnings, sentence_count=NULL, process continues
- [ ] downgrade() function rolls back by setting sentence_count=NULL
- [ ] Unit tests pass for migration logic
- [ ] Runner script supports --downgrade flag

## Manual verification
- Steps:
  1. Create test database with 1000 chunks, all with sentence_count=NULL
  2. Run: python migrations/019_run_migration.py
  3. Monitor logs for progress messages
  4. Verify migration completes successfully
  5. Query: SELECT COUNT(*) FROM chunks WHERE sentence_count IS NOT NULL AND level='chunk';
  6. Verify count matches expected number of content chunks
  7. Spot-check 10 chunks: verify sentence_count accuracy manually
  8. Run migration again (idempotency test)
  9. Verify no changes, log indicates "0 chunks to process"
  10. Run: python migrations/019_run_migration.py --downgrade
  11. Verify all sentence_count values reset to NULL
- Expected results:
  - Migration populates sentence_count for all content chunks
  - Progress logged clearly
  - Re-running migration has no effect (idempotent)
  - Downgrade successfully resets values
  - No errors or crashes during processing

## Notes
- This is the longest-running migration, may take minutes for large databases
- Batch size of 50-100 is recommended based on spec performance requirements
- The migration reads from sanitized_markdown table to get source content
- If sanitized_markdown is missing or hash mismatch occurs, log warning and set sentence_count=NULL
- Follow the exact pattern from migration 010 for consistency
