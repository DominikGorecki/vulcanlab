# Ticket: manual-summarization-flow.T01 - Database Schema and Session Model

## Source

* Spec: documentation/work/manual-summarization-flow.spec.md
* Patterns: documentation/patterns.md

## Goal

* Create the `summarization_sessions` database table with migration
* Add `SummarizationMode` enum to enums.py following existing patterns
* Implement SQLAlchemy model `SummarizationSession` with proper relationships
* Update init_db.py to create the new table

## Scope

### In scope

* Migration file for `summarization_sessions` table with all constraints and indexes
* `SummarizationMode` enum in enums.py with lowercase values matching DB CHECK
* SQLAlchemy model in `src/vulcanlab/data/models/summarization_session.py`
* Registration in `src/vulcanlab/data/models/__init__.py`
* Table creation function in `src/vulcanlab/data/schema/specialized_tables.py`
* Update init_db.py to call new table creation

### Out of scope

* API endpoints (T03)
* Session manager business logic (T03)
* Frontend components (T04)

## Dependencies

* Depends on: none
* Unblocks: T02, T03, T04, T05, T06

## Implementation plan

1. Add `SummarizationMode` enum to `src/vulcanlab/data/models/enums.py`:
   ```python
   class SummarizationMode(str, enum.Enum):
       """
       IMPORTANT: Values MUST match database CHECK constraint exactly (lowercase):
       CHECK (mode IN ('manual', 'automatic'))
       """
       MANUAL = 'manual'
       AUTOMATIC = 'automatic'
   ```

2. Create migration file `migrations/030_add_summarization_sessions.sql`:
   - Table with columns: id, work_id (FK, UNIQUE), mode, status, current_node_index, total_nodes, selected_node_ids (JSONB), created_at, updated_at
   - CHECK constraints for mode and status
   - Index on work_id
   - Foreign key to works(id) with ON DELETE CASCADE

3. Create SQLAlchemy model `src/vulcanlab/data/models/summarization_session.py`:
   - Use mapped_column with proper types
   - Relationship to Work model
   - Import and use SummarizationMode enum

4. Export model from `src/vulcanlab/data/models/__init__.py`

5. Add table creation function to `src/vulcanlab/data/schema/specialized_tables.py`:
   - `create_summarization_sessions_table(conn, app_user, verbose)`
   - Include CHECK constraints matching migration

6. Update `src/vulcanlab/data/init_db.py`:
   - Import new function
   - Call it in proper order (after works table exists)
   - Transfer ownership to app_user

* Patterns to apply:
  * **Enum capitalization**: Lowercase values matching DB CHECK constraints
  * **Migration patterns**: IF NOT EXISTS for idempotency, verification queries at end
  * **Database initialization**: Dual-track (migration + init_db.py modules)

* Deviations (if any):
  * None

## Unit tests (required)

* Add tests for:
  * SummarizationMode enum values match expected lowercase strings
  * SummarizationSession model can be instantiated with valid data
  * Model validates required fields (work_id, mode, status, total_nodes, selected_node_ids)
  * JSONB field selected_node_ids accepts list of integers

* Suggested locations:
  * `tests/unit/data/models/test_summarization_session.py`

* Mocking/fakes needed:
  * Mock database session for model instantiation tests

## Acceptance criteria (checklist)

* [ ] Migration file creates table with all columns and constraints
* [ ] SummarizationMode enum has MANUAL='manual' and AUTOMATIC='automatic'
* [ ] SQLAlchemy model imports and uses the enum correctly
* [ ] Model is exported from models/__init__.py
* [ ] init_db.py creates table on fresh database initialization
* [ ] Unit tests pass for enum and model

## Manual verification

* Steps:
  * Run migration on test database: `psql -f migrations/030_add_summarization_sessions.sql`
  * Verify table exists: `\d summarization_sessions`
  * Run init_db.py on fresh database and verify table creation
  * Test constraint: attempt to insert invalid mode value, expect failure

* Expected results:
  * Table has correct schema with all constraints
  * Foreign key relationship to works table works correctly
  * CHECK constraints reject invalid mode/status values

## Notes

* Requirements covered: R3 (session creation), R9 (session persistence), R16 (session status queryable)
* The status CHECK constraint uses same values as existing SessionStatus enum: 'pending', 'in_progress', 'completed', 'failed'
* UNIQUE constraint on work_id ensures one active session per work
* selected_node_ids stores ordered array of chunk_ids for deterministic node processing order
