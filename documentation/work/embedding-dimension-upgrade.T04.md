# Ticket: embedding-dimension-upgrade.T04 - Create Migration Script for Backup and Status Reset

## Source

* Spec: documentation/work/embedding-dimension-upgrade.spec.md
* Patterns: documentation/patterns.md

## Goal

* Create migration script that backs up affected tables before modification
* Clear all embedding data (required for dimension change)
* Reset `vector_status` from `vec` to `to_vec` so content can be re-embedded
* Provide idempotent, safe migration with clear progress output

## Scope

### In scope

* New migration script `migrations/032_upgrade_embedding_dimensions.py`
* Create `migrations/backups/` directory if not exists
* Backup `chunks` table using PostgreSQL COPY
* Backup `queries` table using PostgreSQL COPY
* Timestamped backup filenames
* Clear `embedding` column in `chunks`
* Clear `embedding_original` and `embedding_hyde` columns in `queries`
* Update `vector_status = 'to_vec'` WHERE `vector_status = 'vec'` in both tables
* Progress messages and summary output

### Out of scope

* `queries.embeddings_mqe` (JSON column, out of scope per spec)
* Actual re-vectorization (user triggers separately)
* Schema ALTER (handled by init_db.py in T03)

## Dependencies

* Depends on: T01, T02 (embedding config and models should be ready)
* Unblocks: none (final ticket)

## Implementation plan

1. Create `migrations/032_upgrade_embedding_dimensions.py`

2. Add standard migration script structure with `main()` entry point

3. Implement backup function:
   - Create `migrations/backups/` directory if not exists
   - Generate timestamp: `datetime.now().strftime("%Y%m%d_%H%M%S")`
   - Use raw psycopg connection for COPY TO (SQLAlchemy doesn't directly support COPY)
   - Backup filenames: `chunks_backup_{timestamp}.sql`, `queries_backup_{timestamp}.sql`
   - Use `COPY {table} TO STDOUT` with CSV format for portability

4. Implement embedding clear function:
   ```sql
   UPDATE chunks SET embedding = NULL;
   UPDATE queries SET embedding_original = NULL, embedding_hyde = NULL;
   ```

5. Implement status reset function:
   ```sql
   UPDATE chunks SET vector_status = 'to_vec' WHERE vector_status = 'vec';
   UPDATE queries SET vector_status = 'to_vec' WHERE vector_status = 'vec';
   ```

6. Add idempotency checks:
   - Check if backup already exists for today (warn but continue)
   - Check if embeddings already NULL (skip clear step)
   - Status reset is naturally idempotent

7. Add progress output:
   - Print each step as it executes
   - Print row counts affected
   - Print backup file paths
   - Print summary at end

8. Add error handling:
   - Fail fast if backup directory not writable
   - Backup must complete before any modifications
   - Wrap modifications in transaction

* Patterns to apply:
   * Migration Scripts for Data Backfill - per patterns.md section 5.2
   * Migration File Naming - `NNN_description.py` format

* Deviations (if any):
   * None

## Unit tests (required)

* Add tests for:
   * `test_migration_creates_backup_directory()` - verify directory creation
   * `test_migration_generates_timestamped_filename()` - verify filename format
   * `test_migration_clears_embeddings()` - verify UPDATE sets columns to NULL
   * `test_migration_resets_vector_status()` - verify status changed from 'vec' to 'to_vec'
   * `test_migration_idempotent_status_reset()` - running twice doesn't cause errors
   * `test_migration_fails_if_backup_dir_not_writable()` - verify fail-fast behavior

* Suggested locations:
   * `tests/unit/test_migration_032.py`

* Mocking/fakes needed:
   * Mock database connection and cursor
   * Mock `conn.execute()` to capture SQL statements
   * Mock filesystem for backup directory tests
   * Mock `os.access()` for permission checks

## Acceptance criteria (checklist)

* [ ] Migration script exists at `migrations/032_upgrade_embedding_dimensions.py`
* [ ] Running script creates `migrations/backups/` directory
* [ ] Backup files created with timestamp in filename
* [ ] Backup uses PostgreSQL COPY for efficiency
* [ ] All embeddings set to NULL in `chunks` table
* [ ] All embeddings set to NULL in `queries` table (original and hyde)
* [ ] `vector_status` updated from `vec` to `to_vec` in both tables
* [ ] Script prints progress messages
* [ ] Script is idempotent (safe to run multiple times)
* [ ] Script fails fast if backup directory not writable
* [ ] Unit tests pass

## Manual verification

* Steps:
   * Ensure database has existing embeddings and `vector_status = 'vec'` rows
   * Run: `python migrations/032_upgrade_embedding_dimensions.py`
   * Check `migrations/backups/` for backup files
   * Query: `SELECT COUNT(*) FROM chunks WHERE embedding IS NOT NULL` (should be 0)
   * Query: `SELECT COUNT(*) FROM chunks WHERE vector_status = 'vec'` (should be 0)
   * Query: `SELECT COUNT(*) FROM chunks WHERE vector_status = 'to_vec'` (should be > 0)
   * Run `python -m vulcanlab.data.init_db -v` to apply schema changes (T03)
   * Verify dimension alteration in logs

* Expected results:
   * Backup files exist in `migrations/backups/`
   * No rows with non-NULL embeddings
   * All previously `vec` rows now `to_vec`
   * init_db.py successfully alters dimensions (since embeddings are NULL)

## Notes

* Requirements covered: R5, R6
* The spec mentions Open Question Q1 about `embeddings_mqe` JSON column - currently scoped out
* COPY TO requires superuser or file permissions; if not available, fall back to SELECT INTO OUTFILE or pg_dump
* The migration must run BEFORE init_db.py (T03) since ALTER TYPE on non-NULL vector columns would fail
* Backup files contain table data; stored locally only (no cloud/remote)
* Expected workflow: Run this script -> Run init_db.py -> User runs vectorization
