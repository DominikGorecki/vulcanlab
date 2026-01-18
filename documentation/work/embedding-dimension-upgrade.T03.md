# Ticket: embedding-dimension-upgrade.T03 - Add Dimension Detection and Alteration to init_db.py

## Source

* Spec: documentation/work/embedding-dimension-upgrade.spec.md
* Patterns: documentation/patterns.md

## Goal

* Add `ensure_vector_dimensions()` function to detect and alter vector column dimensions
* Drop and recreate HNSW indexes after dimension change (indexes are dimension-specific)
* Integrate into init_db.py initialization flow

## Scope

### In scope

* New function `ensure_vector_dimensions()` in `src/vulcanlab/data/schema/indexes.py`
* Query `pg_attribute.atttypmod` to detect current vector dimensions
* ALTER COLUMN statements to change vector dimensions to 1536
* Drop/recreate HNSW indexes after dimension change
* Call from init_db.py before `create_vector_indexes()`
* Logging when dimension alteration occurs

### Out of scope

* Migration script for data backup/reset (T04)
* Embedding model changes (T01)
* SQLAlchemy model changes (T02)

## Dependencies

* Depends on: T02 (SQLAlchemy models should reflect 1536 for consistency)
* Unblocks: T04

## Implementation plan

1. Open `src/vulcanlab/data/schema/indexes.py`

2. Add new function `ensure_vector_dimensions()`:
   ```python
   def ensure_vector_dimensions(target_dim: int = 1536, verbose: bool = False) -> None:
   ```

3. Implement dimension detection using `pg_attribute`:
   ```sql
   SELECT a.attname, a.atttypmod
   FROM pg_attribute a
   JOIN pg_class c ON a.attrelid = c.oid
   WHERE c.relname = 'chunks' AND a.attname = 'embedding'
   ```
   Note: For vector type, `atttypmod` encodes the dimension

4. Define the columns to check:
   - `chunks.embedding`
   - `queries.embedding_original`
   - `queries.embedding_hyde`

5. For each column, if dimension != target_dim:
   - Log the mismatch
   - Drop the HNSW index (dimension-specific): `DROP INDEX IF EXISTS ix_*_hnsw`
   - Execute ALTER: `ALTER TABLE {table} ALTER COLUMN {column} TYPE vector({target_dim})`
   - Log success

6. Open `src/vulcanlab/data/init_db.py` and add call to `ensure_vector_dimensions()` before `create_vector_indexes()`

7. The existing `create_vector_indexes()` will recreate the HNSW indexes with new dimensions

* Patterns to apply:
   * Schema Changes in init_db.py - idempotent patterns per patterns.md section 5.2
   * Database Initialization Module Structure - new function in schema/indexes.py per section 5.1

* Deviations (if any):
   * None

## Unit tests (required)

* Add tests for:
   * `test_ensure_vector_dimensions_detects_768()` - mock pg_attribute query returning 768, verify ALTER is executed
   * `test_ensure_vector_dimensions_skips_when_1536()` - mock query returning 1536, verify no ALTER executed
   * `test_ensure_vector_dimensions_drops_indexes_before_alter()` - verify DROP INDEX called before ALTER
   * `test_ensure_vector_dimensions_handles_null_embedding_column()` - verify graceful handling if column not found

* Suggested locations:
   * `tests/unit/test_schema_indexes.py` (create if not exists)

* Mocking/fakes needed:
   * Mock `engine.connect()` and connection object
   * Mock `conn.execute()` to capture SQL statements
   * Mock return values for dimension detection query

## Acceptance criteria (checklist)

* [ ] `ensure_vector_dimensions()` function exists in `schema/indexes.py`
* [ ] Function queries `pg_attribute` to detect current vector dimensions
* [ ] Function alters columns to 1536 if current dimension differs
* [ ] Function drops HNSW indexes before altering (to avoid dimension mismatch errors)
* [ ] Function logs when dimension alteration occurs
* [ ] `init_db.py` calls `ensure_vector_dimensions()` before `create_vector_indexes()`
* [ ] Unit tests pass

## Manual verification

* Steps:
   * Ensure database has 768-dimension columns (pre-migration state)
   * Run: `python -m vulcanlab.data.init_db -v`
   * Check output for dimension alteration log messages
   * Query database: `SELECT atttypmod FROM pg_attribute WHERE attname = 'embedding' AND attrelid = 'chunks'::regclass`

* Expected results:
   * Log output shows dimension alteration from 768 to 1536
   * Database query confirms new dimension (atttypmod encodes 1536)
   * HNSW indexes exist after init_db completes

## Notes

* Requirements covered: R4, R7
* PostgreSQL vector type stores dimension in `atttypmod`; the encoding is `dim + 4` (so 768 = 772, 1536 = 1540)
* ALTER COLUMN TYPE on vector columns requires NULL values or compatible data; migration script (T04) clears data first
* Existing `dump_db_schema.py` has patterns for querying vector dimensions that can be referenced
* The function should be idempotent - running multiple times should be safe
