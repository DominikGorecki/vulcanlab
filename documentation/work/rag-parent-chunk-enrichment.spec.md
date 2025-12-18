# Title: RAG Parent-Chunk Enrichment and Consolidation Refactor

## Summary
- Replace local markdown file dependency with parent-chunk-based enrichment in retrieval and consolidation stages
- Implement word-count-driven parent traversal algorithm to ensure retrieved chunks meet minimum content requirements
- Add `max_word_count` setting to limit enriched chunk size while preserving complete sentences and headings
- Remove deprecated settings (`min_char_count`, `min_content_length`, `enrich_lines_above`, `enrich_lines_below`, `enrich_from_md`) with backwards compatibility
- Expose `coverage_threshold` in RAG Settings UI
- Update all RAG config presets via migration and ensure init_db.py reflects clean schema for fresh installs

## Problem / Context
- The current RAG retrieval and consolidation pipeline depends on reading local sanitized markdown files to enrich short chunks and fill structural gaps
- This dependency creates a limitation: "Simple Conversion" documents (where sanitized content exists only in the database) cannot use these structural optimizations
- The enrichment process uses line-based metrics (`enrich_lines_above`, `enrich_lines_below`) and character counts (`min_char_count`, `min_content_length`) which are inconsistent with the word-based filtering (`min_word_count`)
- Users cannot configure `coverage_threshold` from the UI, limiting control over parent-level replacement behavior
- The system needs a unified, database-driven approach that works for all document types and uses consistent metrics

**User Impact**: Users processing Simple Conversion documents receive lower-quality context. Users cannot fine-tune consolidation behavior without direct database access.

**Business Impact**: Limits the effectiveness of the RAG system for certain document types and reduces user control over retrieval quality.

## Goals
- Eliminate dependency on local sanitized markdown files for retrieval enrichment and consolidation
- Implement parent-chunk traversal algorithm that walks up the hierarchy until `min_word_count` is met
- Ensure enriched chunks stay within `max_word_count` while preserving sentence and heading integrity
- Migrate all existing RAG config presets to the new schema with backwards compatibility (deprecated keys preserved)
- Update init_db.py to create clean configs (without deprecated keys) for fresh installs
- Expose `coverage_threshold` setting in RAG Settings UI
- Update documentation to reflect the new parent-chunk-based approach

## Non-goals (Strict)
- Changing the core retrieval algorithms (RRF, BGE reranking, MMR)
- Modifying the consolidation grouping logic (hierarchical analysis by `work_id` and `parent_id`)
- Implementing new reranking or scoring mechanisms
- Adding integration tests (unless explicitly requested)
- Changing the database schema for the chunks table
- Implementing new UI components beyond exposing `coverage_threshold`

## Scope

### In scope
- Core retrieval enrichment refactor in `src/vulcanlab/retrieval/retrieve.py`
- Consolidation adjacency merging refactor in `src/vulcanlab/augmentation/consolidate_context.py`
- Parent-level replacement using character-count-based coverage calculation
- SQL migration to update all existing `rag_config` presets with new settings and mark deprecated ones
- Update `src/vulcanlab/data/init_db.py` to use clean config schema for fresh installs
- Add `coverage_threshold` control to RAG Settings UI in `vulcanlab_ui`
- Update `documentation/rag-process-details.md` to document new approach
- Unit tests for new enrichment and consolidation logic

### Out of scope
- Integration tests with live database
- Refactoring unrelated RAG pipeline stages
- Performance optimization beyond current implementation
- Adding new RAG configuration parameters beyond those specified
- UI redesign or significant component restructuring
- Changes to vectorization or embedding generation

## Requirements (Functional)

### Retrieval Enrichment (R1-R5)
- R1: For each retrieved chunk, if `word_count < min_word_count`, walk up the parent hierarchy (`parent_id`) until a parent chunk with `word_count >= min_word_count` is found
- R2: If the parent chunk has `word_count <= max_word_count`, include the entire parent chunk content with the parent's title (from `heading_breadcrumbs` for content chunks, or first line of `content` for heading chunks)
- R3: If the parent chunk has `word_count > max_word_count`, use a sliding window centered on the original chunk, truncating content above and below while:
  - Preserving all headings in the parent chunk (do not truncate lines that are markdown headings)
  - Preserving complete sentences (do not break mid-sentence)
  - Staying as close to `max_word_count` as possible without exceeding it unless necessary to preserve sentence integrity
- R4: If no parent meeting `min_word_count` is found (reached root), use the topmost parent chunk reached, even if below `min_word_count`
- R5: Add new setting `max_word_count` (default: 750) to retrieval config section

### Consolidation (R6-R8)
- R6: For adjacency merging within a parent group, use the shared parent chunk's content instead of reading local markdown files, extracting the range between child chunks using `start_line` and `end_line` attributes
- R7: For parent-level replacement, calculate coverage as: `(sum of character counts in all child chunks in group) / (parent chunk character count)`. If coverage > `coverage_threshold`, replace the entire group with the parent chunk content including its title
- R8: All consolidated groups must retain their heading chain (breadcrumbs): use `heading_breadcrumbs` for content chunks, or first line of `content` for heading chunks

### Settings and Migration (R9-R12)
- R9: Mark the following settings as deprecated (keep in existing presets but do not include in fresh installs): `min_char_count`, `min_content_length`, `enrich_lines_above`, `enrich_lines_below`, `enrich_from_md`
- R10: Create a SQL migration that adds `max_word_count: 750` to the retrieval section of all existing presets in `rag_config` table
- R11: Update `src/vulcanlab/data/init_db.py` function `create_default_rag_config()` to use the new schema without deprecated keys
- R12: Implementation must gracefully handle presets that still contain deprecated keys (backwards compatibility)

### UI (R13)
- R13: Add `coverage_threshold` as a configurable slider/input in the RAG Settings UI consolidation section, with range 0.0-1.0, step 0.05, default 0.5

## Requirements (Non-functional)

### Performance
- Enrichment process must not significantly increase retrieval latency (target: <10% increase for typical queries)
- Parent traversal must be efficient (use database joins or recursive queries where appropriate, avoid N+1 queries)
- Sentence boundary detection for truncation should be lightweight (simple regex or spaCy if already available)

### Reliability
- If parent chunk data is missing or malformed, fall back to using the original chunk without enrichment rather than failing
- Migration must be idempotent (can be run multiple times without causing errors or duplicate updates)
- Settings validation should warn if deprecated keys are present but not fail

### Security / Privacy
- No new security considerations (operating on existing database content)
- Ensure migration runs with appropriate user permissions (app user, not admin)

### Observability
- Log when parent traversal reaches root without meeting `min_word_count`
- Log when chunks are filtered out due to inability to enrich
- Include metrics in retrieval logs: average parent depth traversed, percentage of chunks enriched

## Proposed Solution (High-level)

### Architecture
The solution refactors two key stages of the RAG pipeline:

1. **Retrieval Enrichment (Bridge stage)**:
   - After RRF fusion produces the shortlist, iterate through each chunk
   - For short chunks (< `min_word_count`), traverse parent_id chain until finding adequate parent
   - Apply sliding window algorithm if parent exceeds `max_word_count`
   - Return enriched chunk with proper title

2. **Consolidation**:
   - Groups remain organized by `work_id` and `parent_id` (no change)
   - Adjacency merging uses parent chunk content to bridge gaps (replace file reads)
   - Parent-level replacement uses character-based coverage calculation on chunk content

3. **Configuration Migration**:
   - SQL migration updates existing JSONB configs in rag_config table
   - init_db.py creates clean schema for fresh installs
   - Code handles both old and new schema versions

### Main Components
- **Parent Traversal Algorithm** (`retrieval/retrieve.py`): New function `enrich_chunk_from_parent()` that walks parent chain
- **Sliding Window Truncator** (`retrieval/retrieve.py`): New function `truncate_to_word_limit()` that intelligently trims content
- **Consolidation Refactor** (`augmentation/consolidate_context.py`): Update merging logic to use parent chunks instead of file reads
- **Migration Script** (`migrations/021_add_max_word_count_to_rag_config.sql`): SQL migration for existing presets
- **UI Component Update** (`vulcanlab_ui/src/components/settings/`): Add coverage_threshold control

### Data Flow
```
Retrieved Chunk (from RRF)
  → Check word_count < min_word_count
    → YES: Traverse parent_id chain (enrich_chunk_from_parent)
      → Find parent with word_count >= min_word_count
      → Check parent word_count <= max_word_count
        → YES: Use full parent chunk
        → NO: Apply sliding window (truncate_to_word_limit)
    → NO: Use chunk as-is
  → Send enriched chunks to BGE Reranking
  → After MMR selection, consolidate
    → Group by parent_id
    → Merge adjacent chunks using parent content
    → Calculate coverage, replace with parent if threshold met
  → Format for augmentation
```

## Interfaces / APIs / Contracts

### Internal Function Signatures (New)

```python
# In src/vulcanlab/retrieval/retrieve.py
def enrich_chunk_from_parent(
    chunk: Chunk,
    session: Session,
    min_word_count: int,
    max_word_count: int
) -> dict[str, Any]:
    """
    Enrich a chunk by traversing parent hierarchy.

    Returns:
        dict with keys: 'content', 'title', 'parent_id', 'enriched'
    """
    pass

def truncate_to_word_limit(
    content: str,
    original_chunk_start: int,
    original_chunk_end: int,
    max_word_count: int
) -> str:
    """
    Truncate content using sliding window, preserving sentences and headings.

    Returns:
        Truncated content string
    """
    pass
```

### RAG Config Schema (Updated)

```json
{
  "retrieval": {
    "dense_limit": 19,
    "lexical_limit": 5,
    "rrf_k": 50,
    "top_k_rrf": 75,
    "top_n_final": 17,
    "entity_boost": 0.05,
    "min_word_count": 150,
    "max_word_count": 750,
    "mmr_lambda": 0.7,
    "reranker_batch_size": 8,
    "reranker_max_length": 512,
    "min_sentence_filter_enabled": false,
    "min_sentence_count": 5,
    "_deprecated": {
      "min_char_count": 250,
      "min_content_length": 750,
      "enrich_lines_above": 0,
      "enrich_lines_below": 13
    }
  },
  "consolidation": {
    "coverage_threshold": 0.5,
    "line_gap": 7,
    "min_content_length": 350,
    "_deprecated": {
      "enrich_from_md": true
    }
  },
  "augmentation": {
    "top_n_contexts": 5
  }
}
```

Note: For backwards compatibility, deprecated keys may exist at the top level of `retrieval` and `consolidation` sections. Implementation should check both locations.

### UI Component Props (New)

```typescript
// In vulcanlab_ui/src/components/settings/ConsolidationSettings.tsx
interface ConsolidationSettingsProps {
  coverageThreshold: number;
  onCoverageThresholdChange: (value: number) => void;
  // ... existing props
}
```

## Data Model / Storage

### Database Changes
- **No schema changes required** to the chunks table or rag_config table structure
- Migration updates existing JSONB content in `rag_config.config` column

### Migration Details
- Migration file: `migrations/021_add_max_word_count_to_rag_config.sql`
- Operations:
  1. Add `max_word_count: 750` to all presets' `config->'retrieval'` JSONB
  2. Move deprecated keys to `_deprecated` nested object (if not already there)
  3. Ensure idempotency with conditional updates

### Models Affected
- `RagConfig` model: No changes to model definition, only JSONB content structure

## UX / Workflows

### User-Facing Changes
1. **RAG Settings UI**: Users will see a new "Coverage Threshold" slider in the Consolidation section
   - Label: "Parent Coverage Threshold"
   - Description: "Percentage of parent section required before replacing fragments (0.0-1.0)"
   - Default: 0.5
   - Range: 0.0 to 1.0, step 0.05

2. **Retrieval Behavior**: Users will notice improved context quality for Simple Conversion documents without any action required

3. **Performance**: Slight improvement in retrieval speed (no file I/O), but should be imperceptible to users

### Admin Workflows
- Database administrators applying the migration: Run `migrations/021_add_max_word_count_to_rag_config.sql` as app user
- Fresh installs: Run `init_db.py` as usual; it will create presets with clean schema

## Testing Plan

### Unit Tests

#### Retrieval Enrichment Tests (`tests/unit/test_enrich_from_parent.py`)
- Test parent traversal stops at first parent meeting `min_word_count`
- Test parent traversal reaches root when no parent meets minimum
- Test full parent inclusion when `word_count <= max_word_count`
- Test sliding window truncation when `word_count > max_word_count`
- Test heading preservation in sliding window
- Test sentence boundary preservation
- Test title extraction from `heading_breadcrumbs` for content chunks
- Test title extraction from first line of content for heading chunks
- Mock database session and chunk hierarchy

#### Consolidation Tests (`tests/unit/test_consolidate_parent_chunks.py`)
- Test adjacency merging using parent chunk content
- Test parent-level replacement when coverage exceeds threshold
- Test coverage calculation using character counts
- Test handling of groups with same `parent_id`
- Test heading chain retention in consolidated groups
- Mock chunk data with parent relationships

#### Migration Tests (`tests/unit/test_migration_021.py`)
- Test migration adds `max_word_count` to all presets
- Test migration is idempotent (can run twice)
- Test migration handles presets with missing retrieval section
- Test migration preserves other config values
- Use in-memory SQLite or mock database

### Integration Tests
- Not included in this spec per non-goals

### Manual Test Plan
- [ ] Apply migration to test database with multiple RAG presets
- [ ] Verify all presets have `max_word_count: 750` in retrieval config
- [ ] Run fresh `init_db.py` and verify default preset has clean schema (no deprecated keys)
- [ ] Test retrieval with Simple Conversion document and verify enrichment works
- [ ] Test retrieval with short chunks and verify parent traversal
- [ ] Test retrieval with very long parent chunks and verify truncation preserves headings/sentences
- [ ] Test consolidation with adjacent chunks and verify parent-based merging
- [ ] Test consolidation with high coverage and verify parent replacement
- [ ] Open RAG Settings UI and verify `coverage_threshold` slider appears and functions correctly
- [ ] Change `coverage_threshold` value and verify it saves to database
- [ ] Run end-to-end RAG query and verify context quality is maintained or improved

## Acceptance Criteria (Checklist)
- [ ] Retrieval enrichment uses parent chunks instead of reading local markdown files
- [ ] Parent traversal algorithm walks up hierarchy until `min_word_count` is met or root is reached
- [ ] Sliding window truncation preserves complete sentences and all headings
- [ ] Sliding window respects `max_word_count` while preserving sentence integrity
- [ ] Consolidation adjacency merging uses parent chunk content based on `start_line` and `end_line`
- [ ] Parent-level replacement uses character-count-based coverage calculation
- [ ] Coverage threshold comparison correctly triggers parent replacement when exceeded
- [ ] Migration `021_add_max_word_count_to_rag_config.sql` adds `max_word_count: 750` to all existing presets
- [ ] Migration is idempotent and can be safely re-run
- [ ] `init_db.py` creates default preset with clean schema (no deprecated keys)
- [ ] Code gracefully handles presets with deprecated keys for backwards compatibility
- [ ] `coverage_threshold` control is visible and functional in RAG Settings UI
- [ ] RAG Settings UI correctly saves and loads `coverage_threshold` value
- [ ] Documentation `rag-process-details.md` is updated to reflect parent-chunk-based approach
- [ ] All unit tests pass for enrichment logic
- [ ] All unit tests pass for consolidation logic
- [ ] Manual testing confirms improved context quality for Simple Conversion documents

## Rollout / Migration Plan

### Migration Execution
1. **Backup**: Take database backup before applying migration (standard practice)
2. **Apply Migration**: Run `migrations/021_add_max_word_count_to_rag_config.sql` as app user
3. **Verify**: Query `rag_config` table to confirm all presets have `max_word_count`
4. **Deploy Code**: Deploy updated retrieval and consolidation code
5. **Monitor**: Watch logs for parent traversal metrics and any enrichment failures

### Rollback Plan
- If migration fails: Restore from backup
- If code has bugs: Revert deployment; migration changes are additive and won't break old code
- Deprecated keys are preserved, so rolling back code will use old enrichment logic if needed

### Fresh Install Considerations
- Fresh installs using updated `init_db.py` will have clean config schema
- No special rollout needed for fresh installs

## Risks and Alternatives

### Risks
1. **Parent data quality**: If chunks have missing or incorrect `parent_id` relationships, enrichment will fail
   - Mitigation: Fall back to original chunk if parent chain is broken
2. **Performance regression**: Walking parent hierarchy could add latency
   - Mitigation: Use efficient queries (JOIN or recursive CTE), measure impact in testing
3. **Sentence boundary detection**: Simple regex may not handle all edge cases
   - Mitigation: Use spaCy sentence tokenizer if available (already in dependencies)
4. **Migration complexity**: Updating JSONB fields in PostgreSQL can be tricky
   - Mitigation: Test migration thoroughly on copy of production data

### Alternatives Considered
1. **Keep local file dependency, only refactor for Simple Conversion**
   - Rejected: Would create two code paths and increase maintenance burden
2. **Store enriched content in chunks table**
   - Rejected: Would bloat database and require schema migration
3. **Use character counts instead of word counts for consistency**
   - Rejected: Word counts are more intuitive for users and already in use
4. **Remove deprecated keys immediately**
   - Rejected: User requested backwards compatibility to avoid breaking existing custom presets

## Patterns and Standards Alignment (from documentation/patterns.md)

### Patterns Applied
- **Core Module Independence**: All enrichment and consolidation logic in `src/vulcanlab` (no FastAPI imports)
- **Session Management**: Database sessions passed explicitly to enrichment functions
- **Three-tier Architecture**: Core logic in `vulcanlab`, API exposure in `vulcanlab_api`, UI in `vulcanlab_ui`
- **SQL Migrations**: Using SQL file for config migration (follows pattern in `migrations/013_create_rag_config.sql`)
- **Unit Test Isolation**: Unit tests mock database sessions and do not connect to real database
- **Naming Conventions**: Python snake_case for functions, PascalCase for React components

### Deviations (if any)
- None: This implementation fully complies with documented patterns

## Implementation Notes (Non-binding)

### Suggested Implementation Order
1. Implement `truncate_to_word_limit()` helper function (pure function, easy to test)
2. Implement `enrich_chunk_from_parent()` with parent traversal logic
3. Write unit tests for enrichment functions
4. Refactor consolidation adjacency merging to use parent chunks
5. Update parent-level replacement coverage calculation
6. Write unit tests for consolidation changes
7. Create migration SQL file and test on copy of database
8. Update `init_db.py` default config
9. Add `coverage_threshold` to UI settings component
10. Update documentation
11. Run full manual test plan

### Code Location Hints
- Retrieval enrichment: `src/vulcanlab/retrieval/retrieve.py` (likely in or near existing quality filtering logic)
- Consolidation: `src/vulcanlab/augmentation/consolidate_context.py` (look for existing merge logic)
- RAG Settings UI: `vulcanlab_ui/src/components/settings/` or similar
- Migration: `migrations/021_add_max_word_count_to_rag_config.sql`

### Sentence Boundary Detection
- Prefer spaCy sentence tokenizer if available: `nlp = spacy.load("en_core_web_sm"); sentences = [sent.text for sent in nlp(text).sents]`
- Fallback to regex if needed: `re.split(r'(?<=[.!?])\s+', text)`

### Heading Detection for Preservation
- Use regex to identify markdown headings: `re.match(r'^#{1,6}\s+', line)`
- Preserve entire line if it matches heading pattern

### Parent Traversal Efficiency
- Use SQLAlchemy relationships if defined on Chunk model
- Alternatively, use recursive CTE in raw SQL for efficiency:
  ```sql
  WITH RECURSIVE parent_chain AS (
    SELECT * FROM chunks WHERE id = :chunk_id
    UNION ALL
    SELECT c.* FROM chunks c
    INNER JOIN parent_chain pc ON c.id = pc.parent_id
    WHERE pc.parent_id IS NOT NULL
  )
  SELECT * FROM parent_chain WHERE word_count >= :min_word_count LIMIT 1;
  ```

## Open Questions
- Q1: Should we add observability metrics to track average parent depth traversed?
  - Suggested: Yes, add logging in enrichment function with depth counter
- Q2: Should coverage_threshold UI control include a visual indicator of what the percentage means?
  - Suggested: Add tooltip with explanation: "0.5 means 50% of parent section content must be retrieved"
