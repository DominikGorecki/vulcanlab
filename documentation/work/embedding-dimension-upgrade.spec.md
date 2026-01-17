# Title: Embedding Dimension Upgrade to 1536

## Summary

- Upgrade all vector embedding columns from 768 to 1536 dimensions
- Switch embedding model to Gemini `gemini-embedding-001` with `output_dimensionality=1536`
- Create migration script to backup affected tables and reset embedding data
- Update `init_db.py` to detect and alter vector column dimensions if not 1536
- Clear existing embeddings and reset `vector_status` from `vec` to `to_vec`

## Problem / Context

- The system currently uses 768-dimension embeddings (Gemini `text-embedding-004` or OpenAI `text-embedding-3-small` truncated)
- 1536 dimensions provide richer semantic representation for complex academic/technical content
- Switching to Gemini's `gemini-embedding-001` model offers better embedding quality at 1536 dimensions
- Existing embeddings in the database are incompatible with the new dimension size and must be regenerated

## Goals

- Upgrade embedding dimension from 768 to 1536 across all vector columns
- Use Gemini `gemini-embedding-001` with `output_dimensionality=1536` as the embedding model
- Provide safe migration path with full table backups before data modification
- Make `init_db.py` self-healing: detect dimension mismatch and alter columns automatically
- Reset vectorization status so existing content can be re-embedded

## Non-goals (Strict)

- Preserving existing 768-dimension embeddings (they will be cleared)
- Supporting mixed dimensions within the same database
- Backward compatibility with 768-dimension embeddings
- Migrating embeddings without re-vectorization (not possible due to dimension change)

## Scope

### In scope

- `chunks.embedding` column (Vector)
- `queries.embedding_original` column (Vector)
- `queries.embedding_hyde` column (Vector)
- SQLAlchemy model updates (`chunk.py`, `query.py`)
- `llm_factory.py` embedding model configuration
- `init_db.py` dimension detection and alteration logic
- Migration script for backup and status reset
- HNSW index recreation (indexes must match new dimension)

### Out of scope

- `queries.embeddings_mqe` (JSON array, not a Vector column - unchanged)
- UI changes
- API changes
- Re-running vectorization (user will trigger separately)

## Requirements (Functional)

- R1: Update `llm_factory.py` to use `gemini-embedding-001` model with `output_dimensionality=1536` for Gemini provider
- R2: Update `llm_factory.py` to use `text-embedding-3-small` with `dimensions=1536` for OpenAI provider (fallback)
- R3: Update SQLAlchemy models to declare `Vector(1536)` instead of `Vector(768)`
- R4: Update `init_db.py` to detect current vector column dimension and ALTER to 1536 if different
- R5: Create migration script that:
  - Backs up `chunks` table to SQL file in `migrations/backups/`
  - Backs up `queries` table to SQL file in `migrations/backups/`
  - Sets `embedding = NULL` for all rows in both tables
  - Updates `vector_status = 'to_vec'` WHERE `vector_status = 'vec'` in both tables
- R6: Migration backup files must include timestamp in filename
- R7: `init_db.py` must recreate HNSW indexes after dimension change (indexes are dimension-specific)

## Requirements (Non-functional)

- Performance:
  - Backup should use PostgreSQL COPY for efficiency on large tables
  - ALTER COLUMN operation may lock table briefly; acceptable for maintenance window

- Reliability:
  - Migration script must be idempotent (safe to run multiple times)
  - Backup must complete successfully before any modifications
  - Script should fail fast if backup directory is not writable

- Security / Privacy:
  - Backup files contain table data; stored locally in `migrations/backups/`
  - No credentials in backup filenames

- Observability:
  - Migration script should print progress messages
  - `init_db.py` should log when dimension alteration occurs

## Proposed Solution (High-level)

- **Phase 1**: Update `llm_factory.py` to use new embedding model and dimensions
- **Phase 2**: Update SQLAlchemy models to reflect new dimension
- **Phase 3**: Add dimension detection and ALTER logic to `init_db.py`
- **Phase 4**: Create Python migration script for backup and status reset
- **Phase 5**: Test end-to-end by running migration then `init_db.py`

### Data Flow

1. User runs migration script `python migrations/032_upgrade_embedding_dimensions.py`
2. Script backs up `chunks` and `queries` tables to `migrations/backups/`
3. Script clears embeddings and resets `vector_status`
4. User runs `python -m vulcanlab.data.init_db -v`
5. `init_db.py` detects 768-dimension columns and ALTERs to 1536
6. `init_db.py` recreates HNSW indexes for new dimension
7. User runs vectorization to regenerate embeddings at 1536 dimensions

## Interfaces / APIs / Contracts

- `create_embeddings()` in `llm_factory.py`:
  - Gemini: `GoogleGenerativeAIEmbeddings(model="models/gemini-embedding-001", ..., output_dimensionality=1536)`
  - OpenAI: `OpenAIEmbeddings(model="text-embedding-3-small", dimensions=1536)`

- `create_embeddings_for_provider()` in `llm_factory.py`:
  - Same changes as above for explicit provider selection

## Data Model / Storage

### Tables Affected

| Table | Column | Current | Target |
|-------|--------|---------|--------|
| chunks | embedding | vector(768) | vector(1536) |
| queries | embedding_original | vector(768) | vector(1536) |
| queries | embedding_hyde | vector(768) | vector(1536) |

### Indexes Affected

| Index | Table | Column |
|-------|-------|--------|
| ix_chunks_embedding_hnsw | chunks | embedding |
| ix_queries_embedding_original_hnsw | queries | embedding_original |
| ix_queries_embedding_hyde_hnsw | queries | embedding_hyde |

Note: HNSW indexes are dimension-specific and must be dropped/recreated after ALTER.

## UX / Workflows

Not applicable - this is a backend/database migration with no UI changes.

## Work Breakdown (Ticket Seed)

### Phase 1: Embedding Model Configuration

- T01: Update `llm_factory.py` embedding functions
  - Change Gemini model from `text-embedding-004` to `gemini-embedding-001`
  - Add `output_dimensionality=1536` parameter for Gemini
  - Update OpenAI `dimensions` parameter from 768 to 1536
  - Update both `create_embeddings()` and `create_embeddings_for_provider()`
  - Update docstring comments referencing dimension count

### Phase 2: SQLAlchemy Model Updates

- T02: Update vector column definitions in models
  - `src/vulcanlab/data/models/chunk.py`: Change `Vector(768)` to `Vector(1536)`
  - `src/vulcanlab/data/models/query.py`: Change both `Vector(768)` to `Vector(1536)`
  - Update docstring comments referencing dimension count

### Phase 3: Database Initialization Updates

- T03: Add dimension detection and alteration to `init_db.py`
  - Create new function `ensure_vector_dimensions()` in `schema/indexes.py`
  - Query `pg_attribute` to detect current vector dimensions for each column
  - If dimension != 1536, execute `ALTER TABLE ... ALTER COLUMN ... TYPE vector(1536)`
  - Drop and recreate HNSW indexes after dimension change
  - Call from `init_db.py` before `create_vector_indexes()`

### Phase 4: Migration Script

- T04: Create migration script `migrations/032_upgrade_embedding_dimensions.py`
  - Create `migrations/backups/` directory if not exists
  - Backup `chunks` table using `COPY ... TO` with timestamp filename
  - Backup `queries` table using `COPY ... TO` with timestamp filename
  - Set `embedding = NULL` for all rows in `chunks`
  - Set `embedding_original = NULL, embedding_hyde = NULL` for all rows in `queries`
  - Update `vector_status = 'to_vec'` WHERE `vector_status = 'vec'` in both tables
  - Print progress and summary

### Phase 5: Testing and Documentation

- T05: Test migration end-to-end
  - Verify backups are created correctly
  - Verify embeddings are cleared
  - Verify `vector_status` is updated
  - Verify `init_db.py` alters dimensions
  - Verify indexes are recreated
  - Verify new embeddings can be generated at 1536 dimensions

## Testing Plan

- Unit tests:
  - Test `ensure_vector_dimensions()` detection logic with mock connection
  - Test migration script SQL generation

- Integration tests:
  - Not required per patterns.md

- Manual test plan:
  - Run migration script on test database with existing 768-dim embeddings
  - Verify backup files exist in `migrations/backups/`
  - Verify embeddings are NULL after migration
  - Verify `vector_status` changed from `vec` to `to_vec`
  - Run `init_db.py -v` and verify dimension alteration logged
  - Run vectorization on a small work and verify 1536-dim embeddings stored
  - Verify similarity search still works with new embeddings

## Acceptance Criteria (Checklist)

- [ ] `llm_factory.py` uses `gemini-embedding-001` with `output_dimensionality=1536`
- [ ] `llm_factory.py` OpenAI fallback uses `dimensions=1536`
- [ ] SQLAlchemy models declare `Vector(1536)` for all embedding columns
- [ ] `init_db.py` detects 768-dimension columns and alters to 1536
- [ ] `init_db.py` recreates HNSW indexes after dimension change
- [ ] Migration script creates timestamped backups before modifications
- [ ] Migration script clears all embeddings in `chunks` and `queries`
- [ ] Migration script updates `vector_status` from `vec` to `to_vec`
- [ ] New embeddings can be generated and stored at 1536 dimensions
- [ ] Similarity search works with 1536-dimension embeddings

## Rollout / Migration Plan

1. **Preparation**: Ensure no active vectorization jobs running
2. **Backup**: Run migration script to backup and clear embeddings
3. **Schema Update**: Run `python -m vulcanlab.data.init_db -v`
4. **Verify**: Check logs for dimension alteration and index recreation
5. **Re-vectorize**: Run vectorization for each work that needs embeddings
6. **Validate**: Test similarity search on re-vectorized content

Rollback: Restore from backup files if issues found (manual process)

## Risks and Alternatives

- Risks:
  - Large databases may take significant time to backup and re-vectorize
  - HNSW index recreation locks table briefly
  - Cost: Re-vectorizing all content incurs API costs

- Alternatives considered:
  - Keep 768 dimensions: Rejected - user explicitly requested 1536 for quality
  - Gradual migration: Rejected - mixed dimensions not supported by pgvector indexes
  - Store both dimensions: Rejected - doubles storage, complicates queries

## Patterns and Standards Alignment (from documentation/patterns.md)

- Patterns applied:
  - **Schema Changes in init_db.py**: Using idempotent ALTER patterns per section 5.2
  - **Migration Scripts for Data Backfill**: Using migration script for data modification per section 5.2
  - **Database Initialization Module Structure**: Adding new function to `schema/indexes.py` per section 5.1
  - **Single Source of Truth**: SQLAlchemy models updated alongside init_db changes

- Deviations (if any):
  - None - this follows established patterns

## Implementation Notes (Non-binding)

- Gemini's `GoogleGenerativeAIEmbeddings` accepts `output_dimensionality` parameter (not `dimensions`)
- OpenAI's `OpenAIEmbeddings` accepts `dimensions` parameter
- PostgreSQL `ALTER COLUMN ... TYPE vector(N)` works in-place for NULL values
- For non-NULL values, PostgreSQL would error - hence clearing embeddings first via migration
- The `pg_attribute.atttypmod` encodes vector dimensions; query pattern in existing `dump_db_schema.py`

## Open Questions

- Q1: Should the migration script also handle the `embeddings_mqe` JSON column (contains array of embeddings)? Currently scoped out since it's JSON not Vector, but the dimension change affects the embedded arrays.
