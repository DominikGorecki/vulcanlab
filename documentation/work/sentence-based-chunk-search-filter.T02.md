# Ticket: sentence-based-chunk-search-filter.T02 - Update Content Chunking to Count and Store Sentences

## Source
- Spec: documentation/work/sentence-based-chunk-search-filter.spec.md
- Patterns: documentation/patterns.md

## Goal
- Modify content_chunking.py to count sentences for level='chunk' chunks
- Store sentence_count in database when creating chunks
- Handle errors gracefully without halting the chunking process

## Scope
### In scope
- Update chunk_content() function in src/vulcanlab/chunking/content_chunking.py
- Count sentences using existing _get_sentences() helper for chunks with level='chunk'
- Set sentence_count on Chunk objects before database commit
- Add error handling: log warning and set sentence_count=NULL on counting errors
- Add logging to indicate when sentence_count is set or NULL

### Out of scope
- Counting sentences for non-chunk levels (H1-H5, sentence)
- Modifying the _get_sentences() function itself
- Backfilling existing chunks (separate migration ticket)
- Changing chunking algorithm logic

## Dependencies
- Depends on: T01 (Chunk model must have sentence_count field)
- Unblocks: T05 (manual testing of end-to-end chunking)

## Implementation plan
- Locate the code in src/vulcanlab/chunking/content_chunking.py where Chunk objects are created
- After creating a Chunk with level='chunk', add sentence counting logic:
  - Extract chunk.content
  - Call _get_sentences(content) to get list of sentences
  - Set chunk.sentence_count = len(sentences)
  - Wrap in try/except to catch errors, log warning, set sentence_count=NULL
- For chunks with level != 'chunk', do NOT set sentence_count (leave as NULL/default)
- Add verbose logging: "Counted N sentences for chunk ID X" when successful
- Add warning logging: "Failed to count sentences for chunk: <error>" when errors occur
- Patterns to apply:
  - Core Module: Pure Python logic, no framework dependencies
  - Database session management: Session passed as argument
  - Logging: Use existing logging patterns in the module
- Deviations (if any):
  - None

## Unit tests (required)
- Add tests for:
  - Chunk with level='chunk' has sentence_count populated (mock _get_sentences to return 5 sentences)
  - Chunk with level='H1' does NOT have sentence_count set (remains NULL)
  - Chunk with level='sentence' does NOT have sentence_count set (remains NULL)
  - Error during sentence counting sets sentence_count=NULL and logs warning (mock _get_sentences to raise exception)
  - Chunking process continues even if sentence counting fails for one chunk
  - _get_sentences returns correct count for various text types (multi-sentence, bullets, single sentence)
- Suggested locations:
  - tests/unit/test_content_chunking.py
- Mocking/fakes needed:
  - Mock database session
  - Mock _get_sentences for controlled test cases
  - Mock spaCy nlp for testing error scenarios

## Acceptance criteria (checklist)
- [ ] content_chunking.py counts sentences for level='chunk' chunks only
- [ ] sentence_count is stored in Chunk object before database commit
- [ ] Error handling prevents chunking process from halting on counting errors
- [ ] Logging indicates when sentence_count is set successfully
- [ ] Warning logging indicates when sentence_count is NULL due to errors
- [ ] Non-chunk levels (H1-H5, sentence) do not have sentence_count set
- [ ] Unit tests pass for all sentence counting scenarios
- [ ] Chunking process is not slowed by more than 5% (manual observation)

## Manual verification
- Steps:
  1. Run content_chunking on a test work with sample markdown
  2. Check logs for "Counted N sentences" messages
  3. Query database: SELECT id, level, sentence_count FROM chunks WHERE work_id=X LIMIT 20;
  4. Verify level='chunk' rows have sentence_count populated
  5. Verify level='H1', 'H2', etc. rows have sentence_count=NULL
  6. Create a test with malformed content that causes spaCy error
  7. Verify chunking completes and logs warning
- Expected results:
  - Content chunks have sentence_count > 0
  - Heading chunks have sentence_count = NULL
  - Errors logged but process completes
  - Sentence counts appear accurate (spot-check 5 chunks manually)

## Notes
- The _get_sentences() function already exists and uses spaCy for sentence detection
- Reuse this function to ensure consistency with chunking overlap logic
- Performance: spaCy sentence detection is fast, should add minimal overhead
- The spec mentions this should not add more than 5% overhead to chunking time
