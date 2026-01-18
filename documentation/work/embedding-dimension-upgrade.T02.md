# Ticket: embedding-dimension-upgrade.T02 - Update SQLAlchemy Vector Column Definitions

## Source

* Spec: documentation/work/embedding-dimension-upgrade.spec.md
* Patterns: documentation/patterns.md

## Goal

* Update all SQLAlchemy model Vector column definitions from 768 to 1536 dimensions
* Ensure ORM models match the new embedding size

## Scope

### In scope

* `src/vulcanlab/data/models/chunk.py` - `embedding` column
* `src/vulcanlab/data/models/query.py` - `embedding_original` and `embedding_hyde` columns
* Docstrings/comments referencing dimension count

### Out of scope

* `queries.embeddings_mqe` (JSON column, not Vector)
* Database schema changes (handled by init_db.py in T03)
* Migration script (T04)

## Dependencies

* Depends on: none (can be done in parallel with T01)
* Unblocks: T03, T04

## Implementation plan

1. Open `src/vulcanlab/data/models/chunk.py`:
   - Change `Vector(768)` to `Vector(1536)` on line 56
   - Update docstring comment "embedding: Vector embedding (768 dimensions)" to "1536 dimensions"

2. Open `src/vulcanlab/data/models/query.py`:
   - Change `Vector(768)` to `Vector(1536)` for `embedding_original` on line 49
   - Change `Vector(768)` to `Vector(1536)` for `embedding_hyde` on line 51
   - Update docstring comment "embedding_original: Vector embedding for original query (768 dimensions)" to "1536 dimensions"
   - Update docstring comment referencing dimension count for `embedding_hyde`
   - Update the comment on line 48 "Embeddings (768 dimensions for text-embedding-004)" to reflect new model and dimensions

* Patterns to apply:
   * Single Source of Truth - SQLAlchemy models match init_db schema

* Deviations (if any):
   * None

## Unit tests (required)

* Add tests for:
   * `test_chunk_embedding_column_dimension()` - verify Chunk.embedding is Vector(1536)
   * `test_query_embedding_original_column_dimension()` - verify Query.embedding_original is Vector(1536)
   * `test_query_embedding_hyde_column_dimension()` - verify Query.embedding_hyde is Vector(1536)

* Suggested locations:
   * `tests/unit/test_models.py` (create if not exists)

* Mocking/fakes needed:
   * None - these are static model introspection tests

## Acceptance criteria (checklist)

* [ ] `Chunk.embedding` declared as `Vector(1536)`
* [ ] `Query.embedding_original` declared as `Vector(1536)`
* [ ] `Query.embedding_hyde` declared as `Vector(1536)`
* [ ] Docstrings updated to reference 1536 dimensions
* [ ] Unit tests pass

## Manual verification

* Steps:
   * Run: `python -c "from vulcanlab.data.models.chunk import Chunk; print(Chunk.embedding.type)"`
   * Run: `python -c "from vulcanlab.data.models.query import Query; print(Query.embedding_original.type, Query.embedding_hyde.type)"`

* Expected results:
   * Output shows `VECTOR(1536)` for all embedding columns

## Notes

* Requirements covered: R3
* The `embeddings_mqe` column is JSON (array of embeddings) and is out of scope per spec
* SQLAlchemy model changes alone do not alter the database schema - that requires init_db.py (T03)
