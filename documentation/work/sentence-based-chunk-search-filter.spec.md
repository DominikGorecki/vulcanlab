# Title: Sentence-Based Chunk Search Filter

## Summary
- Add sentence counting capability to content chunks during the chunking process
- Introduce configurable minimum sentence threshold for RAG search filtering
- Store sentence counts in the chunks table with appropriate indexing
- Expose filter controls in the RAG Settings UI (retrieval section)
- Provide migration tooling to backfill sentence counts for existing chunks
- Update both dense and lexical retrieval queries to respect the sentence filter settings

## Problem / Context
- Currently, all content chunks are considered during RAG search regardless of their content density
- Very short chunks (1-2 sentences) may not provide sufficient context for meaningful retrieval
- Users have no way to configure minimum content requirements for chunks in search results
- The system lacks the ability to filter chunks based on sentence count, which could improve retrieval quality by focusing on more substantive content

## Goals
- Enable sentence counting for content chunks using the existing spaCy-based sentence detection
- Allow users to configure a minimum sentence threshold for search filtering
- Provide database-level filtering to improve query performance
- Maintain backward compatibility by making the filter optional (can be disabled)
- Support both fresh installations and existing databases through migrations

## Non-goals (Strict)
- Do not apply sentence filtering to heading-level chunks (H1-H5) or sentence-level chunks
- Do not modify the chunking algorithm's core logic for determining chunk boundaries
- Do not change how sentences are detected (continue using spaCy `en_core_web_sm`)
- Do not add sentence filtering to other parts of the system outside RAG retrieval
- Do not create a UI for bulk recalculation (migration script handles this)

## Scope
### In scope
- Add `sentence_count` column to chunks table (Integer, nullable, indexed)
- Update content_chunking.py to count and store sentences during chunk creation
- Add two new RAG config properties: `min_sentence_filter_enabled` and `min_sentence_count`
- Update RAG Settings UI to expose these two new fields in the retrieval section
- Modify retrieve.py to filter chunks by sentence_count when enabled
- Create migration SQL and Python scripts for schema change and backfill
- Update db_init.py to include sentence_count column for fresh installs and the index just like in migration (migrations are not run on fresh installs)
- Write unit tests for sentence counting logic and retrieval filtering

### Out of scope
- Real-time UI for monitoring sentence count backfill progress
- Sentence filtering in non-RAG contexts (e.g., chunk export, visualization)
- Alternative sentence detection libraries beyond spaCy
- Filtering based on other content metrics (word count, character count, etc.)

## Requirements (Functional)
- R1: The chunks table SHALL have a new `sentence_count` column (Integer, nullable, B-tree indexed)
- R2: The content_chunking module SHALL count sentences using spaCy `_get_sentences()` function for level='chunk' chunks only
- R3: The sentence_count SHALL be stored in the database when content chunks are created
- R4: The rag_config.config JSONB SHALL support `retrieval.min_sentence_filter_enabled` (boolean) and `retrieval.min_sentence_count` (integer)
- R5: The RAG Settings UI SHALL display these two fields in the retrieval section with appropriate labels and validation
- R6: When min_sentence_filter_enabled=true, the retrieve.py module SHALL filter chunks WHERE sentence_count >= min_sentence_count
- R7: When min_sentence_filter_enabled=false, ALL chunks SHALL be considered regardless of sentence_count
- R8: A migration script SHALL exist to add the sentence_count column and create the index
- R9: A separate backfill migration script SHALL populate sentence_count for existing chunks in batches with progress logging
- R10: The db_init.py script SHALL include sentence_count column definition for fresh installations

## Requirements (Non-functional)
- Performance:
  - The B-tree index on sentence_count SHALL be used by query planner for filtering
  - Backfill migration SHALL process works in batches (e.g., 50 chunks per transaction) to avoid memory issues
- Reliability:
  - Sentence counting errors SHALL NOT halt the chunking process; log warning and set sentence_count=NULL
  - Backfill script SHALL be idempotent (safe to re-run if interrupted)
  - Migration SHALL include rollback SQL for schema changes
- Security / Privacy:
  - No new security considerations; sentence counts are non-sensitive metadata
- Observability:
  - Backfill migration SHALL log progress every 100 chunks processed
  - Content chunking SHALL log when sentence_count is NULL due to counting errors
  - Retrieval logging SHALL indicate when sentence filter is active and how many chunks were filtered out

## Proposed Solution (High-level)
- Extend the Chunk model in `src/vulcanlab/data/models/chunk.py` to include `sentence_count: Mapped[Optional[int]]`
- In `src/vulcanlab/chunking/content_chunking.py`, after creating a chunk with level='chunk', count sentences using existing `_get_sentences()` helper
- Store the count in the Chunk object before committing to database
- Add new fields to the default RAG config seed data in migrations or db_init.py
- Update RagConfig JSONB schema documentation to include the new retrieval filter properties
- In `src/vulcanlab/retrieval/retrieve.py`, add conditional WHERE clause to dense and lexical queries based on config settings
- Create migration `migrations/0XX_add_sentence_count.sql` for DDL changes
- Create migration `migrations/0XX_backfill_sentence_count.py` for data population with batch processing
- Update `src/vulcanlab/data/db_init.py` to include sentence_count in chunks table creation
- Add UI fields in `vulcanlab_ui/src/components/settings/` (or appropriate RAG settings component)

## Interfaces / APIs / Contracts
- Chunk model:
  - New field: `sentence_count: Optional[int]` (nullable to handle legacy data and errors)
- RagConfig JSONB structure (retrieval section):
  ```json
  {
    "retrieval": {
      "min_sentence_filter_enabled": false,
      "min_sentence_count": 5,
      "dense_limit": 19,
      "lexical_limit": 5,
      ...
    }
  }
  ```
- RAG Settings API (existing endpoints):
  - GET `/api/v1/rag-config` returns config including new fields
  - PUT `/api/v1/rag-config/{id}` accepts updates to new fields with validation (min_sentence_count >= 1)
- Migration scripts:
  - `migrations/0XX_add_sentence_count.sql` - schema change
  - `migrations/0XX_backfill_sentence_count.py` - data backfill with `run_migration()` entrypoint
  - `migrations/0XX_run_migration.py` - runner script for backfill

## Data Model / Storage
- chunks table changes:
  ```sql
  ALTER TABLE chunks ADD COLUMN sentence_count INTEGER NULL;
  CREATE INDEX idx_chunks_sentence_count ON chunks(sentence_count);
  ```
- rag_config table:
  - No schema change; new properties stored in existing JSONB `config` column
  - Update default config seed data to include new fields
- Indexes:
  - B-tree index on `chunks.sentence_count` for efficient filtering

## UX / Workflows
- RAG Settings page workflow:
  1. User navigates to Settings > RAG Settings
  2. In the retrieval section, user sees new fields:
     - Checkbox: "Enable minimum sentence filter" (maps to min_sentence_filter_enabled)
     - Number input: "Minimum sentences" (maps to min_sentence_count, enabled only when checkbox is checked)
  3. User sets checkbox to enabled and sets minimum to 5
  4. User saves RAG config
  5. Subsequent searches will only consider chunks with sentence_count >= 5
- Backfill migration workflow:
  1. Admin runs migration runner script after upgrading codebase
  2. Script logs: "Processing work 1/50..."
  3. For each work, script reads sanitized markdown, re-chunks in-memory, counts sentences
  4. Script updates existing chunks with sentence counts in batches
  5. Script logs: "Completed: 1000 chunks updated"

## Testing Plan
- Unit tests:
  - Test `_get_sentences()` returns correct count for various text inputs (simple, multi-sentence, bullets, edge cases)
  - Test content_chunking sets sentence_count for level='chunk' chunks
  - Test content_chunking does NOT set sentence_count for non-chunk levels
  - Test retrieval filtering with min_sentence_filter_enabled=true and various thresholds
  - Test retrieval returns all chunks when min_sentence_filter_enabled=false
  - Test RagConfig validation rejects invalid min_sentence_count values (< 1, non-integer)
- Integration tests:
  - Not required for this spec
- Manual test plan:
  - Create a new work and verify sentence_count is populated during chunking
  - Verify sentence counts are accurate by spot-checking 5-10 chunks manually
  - Enable sentence filter in RAG Settings UI and verify filter works in search results
  - Disable sentence filter and verify all chunks are returned
  - Run backfill migration on test database with existing chunks
  - Verify migration logs progress and completes successfully
  - Check database to confirm sentence_count populated for existing chunks

## Acceptance Criteria (Checklist)
- [ ] chunks table has sentence_count column (Integer, nullable, indexed)
- [ ] content_chunking.py counts sentences for level='chunk' chunks and stores in database
- [ ] RagConfig supports min_sentence_filter_enabled and min_sentence_count fields
- [ ] RAG Settings UI displays and allows editing of the two new filter fields
- [ ] retrieve.py filters chunks by sentence_count when filter is enabled
- [ ] retrieve.py ignores sentence_count filter when disabled
- [ ] Migration SQL script adds column and index
- [ ] Backfill migration script populates sentence_count for existing chunks in batches
- [ ] Backfill script logs progress appropriately
- [ ] db_init.py includes sentence_count column for fresh installs
- [ ] Unit tests pass for sentence counting and retrieval filtering
- [ ] Manual testing confirms filter works as expected in UI and search results

## Rollout / Migration Plan
- Step 1: Deploy code changes (Core, API, UI) without running migrations
- Step 2: Run schema migration `0XX_add_sentence_count.sql` to add column and index
- Step 3: Run backfill migration `0XX_run_migration.py` to populate sentence counts for existing chunks
- Step 4: Verify backfill completed successfully by checking database
- Step 5: Update default RAG config to include new fields (if not already seeded)
- Step 6: Users can now enable sentence filtering in RAG Settings UI
- Rollback plan:
  - If issues occur, disable filter via RAG Settings (set min_sentence_filter_enabled=false)
  - If schema rollback needed, run: `ALTER TABLE chunks DROP COLUMN sentence_count;`

## Risks and Alternatives
- Risks:
  - Backfill migration may take significant time for databases with millions of chunks (mitigated by batch processing and progress logging)
  - Sentence detection via spaCy may be inaccurate for certain text types (e.g., code blocks, technical notation)
  - Adding index increases write overhead for chunk insertions (minimal impact given chunking is batch operation)
- Alternatives considered:
  - Store sentence count in JSONB metadata column: Rejected because it's harder to index and query efficiently
  - Count sentences during retrieval on-the-fly: Rejected due to performance overhead on every search
  - Use regex-based sentence detection instead of spaCy: Rejected because we already use spaCy for chunking and it's more accurate
  - Apply filter to all chunk levels: Rejected because heading chunks should always be searchable regardless of length

## Patterns and Standards Alignment (from documentation/patterns.md)
- Patterns applied:
  - Three-tier architecture: Core logic in `src/vulcanlab`, API in `src/vulcanlab_api`, UI in `vulcanlab_ui`
  - Core module independence: sentence counting logic in pure Python, no FastAPI imports
  - Database session management: session passed as argument to functions
  - SQL migrations: DDL changes in `.sql` file, data backfill in `.py` script
  - Configuration dual system: sentence filter settings in vulcanlab.config (RagConfig), not API config
  - Testing strategy: unit tests with mocked DB, no real database connections
- Deviations (if any):
  - None; this spec follows all established patterns

## Implementation Notes (Non-binding)
- The spaCy `_get_sentences()` function is already defined in content_chunking.py and used for sentence detection; reuse this for counting
- Consider using the same sentence detection logic for both chunking overlap and sentence counting to ensure consistency
- The backfill migration should read from `sanitized_markdown` table to get the source text, not from chunks themselves
- For chunks where sanitized_markdown is unavailable or hash mismatches, log a warning and set sentence_count=NULL
- The RAG Settings UI component is likely in `vulcanlab_ui/src/components/settings/` or similar; check existing RAG settings page structure
- Default value for min_sentence_count should be 5 (as mentioned in the prompt)
- When filter is enabled but a chunk has sentence_count=NULL, the chunk should be EXCLUDED from search (conservative approach)

## Open Questions
- Q1: Should the default RAG config have min_sentence_filter_enabled set to true or false initially?
- Q2: What should happen to chunks with sentence_count=NULL when the filter is enabled - include or exclude?
- Q3: Should there be a maximum value validation for min_sentence_count (e.g., <= 50)?
