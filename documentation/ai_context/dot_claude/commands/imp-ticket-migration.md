---

description: Implement a database migration ticket with SQL files, optional Python backfill scripts, and init_db.py updates.
argument-hint: [path/to/migration-ticket.md]
--------------------------------------------

You implement a database migration ticket following VulcanLab's dual-track migration pattern: manual migrations for existing databases AND init_db.py updates for fresh installs.

* $1 = path to a migration ticket file, typically `documentation/work/<ticket-name>.md`.

## Hard requirements

* You MUST read the ticket file ($1) fully before doing anything else.
* You MUST read `documentation/patterns.md` fully before implementing. If it does not exist or is empty, STOP and ask.
* You MUST auto-detect the next migration number by scanning the `migrations/` folder.
* You MUST create migration files in the `migrations/` folder.
* You MUST update `src/vulcanlab/data/init_db.py` to replicate the migration for fresh installs.
* You MUST prefer SQL files (*.sql) over Python unless complex logic is absolutely required.
* You MUST NOT include rollback/downgrade logic (migrations are forward-only).
* You MUST follow the three-tier architecture: Core Module (src/vulcanlab) is framework-independent.
* Use plain output. Do NOT use emojis or icon-like characters.

## Step 1: Validate input

* If $1 is empty, ask for the migration ticket path and STOP.
* If $1 does not exist or is not a Markdown file, ask for a valid ticket path and STOP.

## Step 2: Load context

1. Read the migration ticket ($1) fully.

2. Read `documentation/patterns.md` fully to understand:
   * Database patterns (SQLAlchemy ORM, session management)
   * Core Module constraints (no FastAPI imports)
   * Infrastructure (PostgreSQL 16+, pgvector, AGE extensions)

3. Read `src/vulcanlab/data/init_db.py` to understand:
   * How fresh database initialization works
   * Existing helper functions (create_enums, create_tables, create_*_triggers, etc.)
   * The init_database() orchestration function
   * Patterns for creating indexes, triggers, and seeding data

## Step 3: Auto-detect next migration number

1. Scan the `migrations/` folder for existing migration files.
2. Find the highest migration number (e.g., 019 from `019_add_sentence_count.sql`).
3. Increment by 1 to get the next migration number (e.g., 020).
4. Use three-digit zero-padded format (e.g., 020, 021).

## Step 4: Determine migration complexity

Based on the ticket requirements, determine if this is:

### Simple migration (SQL only)
* Schema changes: ADD COLUMN, CREATE TABLE, CREATE INDEX
* Simple data updates with static values
* Creating triggers or functions with SQL
* Enabling extensions

For simple migrations, create: `migrations/NNN_description.sql`

### Complex migration (SQL + Python)
* Data backfilling requiring Python logic
* Complex calculations or transformations
* Integration with spaCy, LLM processing, or other Python libraries
* Batch processing with progress reporting

For complex migrations, create THREE files:
1. `migrations/NNN_description.sql` - Schema changes
2. `migrations/NNN_backfill_description.py` - Python backfill logic
3. `migrations/NNN_run_migration.py` - Script runner

## Step 5: Implement migration files

### For simple migrations (SQL only):

Create `migrations/NNN_description.sql`:

```sql
-- Migration NNN: <Brief description>
-- <Additional context about what this migration does>
-- NOTE: This migration should be run as the application user to ensure proper ownership

-- Schema changes here
ALTER TABLE table_name ADD COLUMN IF NOT EXISTS column_name TYPE;

-- Indexes
CREATE INDEX IF NOT EXISTS idx_name ON table_name(column_name);

-- Verification query (optional but recommended)
SELECT '<description> created successfully' AS status
WHERE EXISTS (
    SELECT 1 FROM information_schema.columns
    WHERE table_name = 'table_name' AND column_name = 'column_name'
);
```

Key patterns:
* Use `IF NOT EXISTS` / `IF EXISTS` for idempotency
* Include a verification query at the end
* Add clear comments explaining what and why
* Use proper SQL formatting and indentation

### For complex migrations (Python + SQL):

#### File 1: `migrations/NNN_description.sql`

Schema changes only (same pattern as simple migrations above).

#### File 2: `migrations/NNN_backfill_description.py`

Python backfill script following this pattern (based on 019_backfill_sentence_count.py):

```python
"""
Migration NNN: <Brief description>

This migration <describe what it does>.

Changes:
1. <Change 1>
2. <Change 2>
3. <Change 3>

Note: This migration is idempotent and safe to re-run.
"""

import logging
from sqlalchemy import text

# Import any necessary dependencies (spaCy, etc.)
# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Define helper functions if needed

def upgrade(connection):
    """Apply the migration."""
    print("Starting migration NNN: <Brief description>")
    print("=" * 60)

    # Step 1: Get total count of items to process
    result = connection.execute(text("""
        SELECT COUNT(*) FROM table_name WHERE condition
    """))
    total_items = result.scalar()
    print(f"\nTotal items to process: {total_items}")

    if total_items == 0:
        print("No items to process")
        print("=" * 60)
        return

    # Step 2: Process items in batches
    batch_size = 100
    items_processed = 0
    items_updated = 0
    items_with_errors = 0

    print(f"\nProcessing items in batches of {batch_size}...")

    while items_processed < total_items:
        # Fetch batch
        result = connection.execute(
            text("""
                SELECT id, data
                FROM table_name
                WHERE condition
                ORDER BY id
                LIMIT :limit
            """),
            {"limit": batch_size}
        )

        batch = result.fetchall()
        if not batch:
            break

        # Process each item
        updates = []
        for row in batch:
            item_id, data = row
            items_processed += 1

            try:
                # Process data
                processed_value = process_data(data)

                updates.append({
                    'item_id': item_id,
                    'value': processed_value
                })
                items_updated += 1

            except Exception as e:
                logger.warning(f"Error processing item {item_id}: {e}")
                updates.append({
                    'item_id': item_id,
                    'value': None
                })
                items_with_errors += 1

        # Batch update
        for update in updates:
            connection.execute(
                text("UPDATE table_name SET column = :value WHERE id = :id"),
                {"value": update['value'], "id": update['item_id']}
            )
        connection.commit()

        # Progress logging
        if items_processed % 100 == 0 or items_processed == total_items:
            print(f"  Processed {items_processed:,} / {total_items:,} items...")

    # Step 3: Summary
    print("\n" + "=" * 60)
    print("Migration NNN completed successfully!")
    print(f"\nSummary:")
    print(f"  Total items processed: {items_processed:,}")
    print(f"  Items updated: {items_updated:,}")
    print(f"  Items with errors: {items_with_errors:,}")
    print("=" * 60)
```

Key patterns for backfill scripts:
* Use batch processing (default 100 items)
* Include progress logging every 100 items
* Handle errors gracefully (log warning, continue)
* Use parameterized queries to prevent SQL injection
* Commit after each batch
* Provide summary at the end
* Make it idempotent (safe to re-run)

#### File 3: `migrations/NNN_run_migration.py`

Migration runner script (based on 019_run_migration.py):

```python
"""
Migration runner for migration NNN (<brief description>).

This script runs migration NNN which <describe what it does>.

Usage:
    python migrations/NNN_run_migration.py
"""

import sys
import importlib.util
from pathlib import Path

from vulcanlab.data.database import engine


# Load migration module directly from file
migration_path = Path(__file__).parent / "NNN_backfill_description.py"
spec = importlib.util.spec_from_file_location("migration_NNN", migration_path)
migration_NNN = importlib.util.module_from_spec(spec)
spec.loader.exec_module(migration_NNN)

upgrade = migration_NNN.upgrade


def main():
    """Run migration NNN."""
    print("=" * 80)
    print("Migration NNN: <Brief Description>")
    print("=" * 80)
    print()

    print("Running UPGRADE (applying migration)...")
    print()

    try:
        with engine.connect() as connection:
            upgrade(connection)
        print()
        print("✅ Migration NNN upgrade completed successfully!")

    except Exception as e:
        print()
        print(f"❌ ERROR during migration upgrade: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)


if __name__ == "__main__":
    main()
```

## Step 6: Update init_db.py

CRITICAL: Fresh installs do NOT run migrations. The init_db.py file must replicate ALL migration changes.

1. Create a new function in `src/vulcanlab/data/init_db.py` that implements the migration logic:

```python
def create_<descriptive_name>(verbose: bool = False) -> None:
    """
    <Description of what this creates/modifies>

    <Additional context, especially if this replicates a migration>

    Args:
        verbose: If True, print progress information.
    """
    if verbose:
        print("Creating <description>...")

    with engine.connect() as conn:
        # SQL statements here (same as migration SQL)
        conn.execute(text("""
            -- SQL here
        """))

        conn.commit()

    # Transfer ownership to app user if needed
    db_config = load_config().database
    app_user = db_config.app_user

    try:
        with engine.connect() as conn:
            # Transfer function/sequence ownership if created
            conn.execute(text(f'ALTER FUNCTION function_name() OWNER TO "{app_user}"'))
            conn.commit()
            if verbose:
                print(f"Transferred ownership to {app_user}")
    except Exception as e:
        if verbose:
            print(f"Note: Could not transfer ownership: {e}")

    if verbose:
        print("<description> created successfully")
```

2. Add the new function to the `init_database()` orchestration:

```python
def init_database(verbose: bool = False) -> None:
    """
    Initialize the database: create database, user, tables, and indexes.

    Args:
        verbose: If True, print progress information.
    """
    create_database_and_user(verbose=verbose)
    enable_pgvector_extension(verbose=verbose)
    create_enums(verbose=verbose)
    create_tables(verbose=verbose)
    create_io_files_triggers(verbose=verbose)
    create_experiments_triggers(verbose=verbose)
    create_vector_indexes(verbose=verbose)
    create_fulltext_search(verbose=verbose)
    create_history_indexes(verbose=verbose)
    create_prompt_meta_table(verbose=verbose)
    create_result_models_table(verbose=verbose)
    create_collections_table(verbose=verbose)
    create_<your_new_function>(verbose=verbose)  # ADD HERE
    seed_prompt_templates(verbose=verbose)
    seed_default_result_model(verbose=verbose)
    create_default_rag_config(verbose=verbose)

    if verbose:
        print("Database initialization complete")
```

Key patterns for init_db.py:
* Use `IF NOT EXISTS` / `IF EXISTS` for idempotency
* Include verbose logging
* Transfer ownership to app_user for functions/sequences
* Follow existing naming conventions (create_*, seed_*, enable_*)
* Place new function calls in logical order in init_database()
* Use `text()` wrapper for SQL queries
* Commit after changes

### For backfill migrations in init_db.py

If the migration includes a backfill script, you have two options:

#### Option A: Skip backfill in init_db.py
If the backfill only applies to existing data (not fresh installs), document this in the function:

```python
def create_<name>(verbose: bool = False) -> None:
    """
    Add <column> to <table>.

    Note: For existing databases, run migrations/NNN_backfill_description.py
    to populate this column for existing records. Fresh installs do not need
    backfilling as new records will have this column populated automatically.
    """
```

#### Option B: Include simplified backfill logic
If fresh installs need initial data, include simplified logic:

```python
def create_and_seed_<name>(verbose: bool = False) -> None:
    """
    Add <column> to <table> and seed initial data.
    """
    if verbose:
        print("Creating <description>...")

    with engine.connect() as conn:
        # Add column
        conn.execute(text("""
            ALTER TABLE table_name ADD COLUMN IF NOT EXISTS column_name TYPE;
        """))

        # Seed initial data (simplified for fresh installs)
        conn.execute(text("""
            INSERT INTO table_name (columns) VALUES (values);
        """))

        conn.commit()
```

## Step 7: Implementation order

Implement files in this order:

1. Create migration SQL file(s) first
2. Create Python backfill script if needed
3. Create migration runner if needed
4. Update init_db.py with new function
5. Add function call to init_database()
6. Test by reviewing the code (no automated testing required)

## Step 8: Report back

After implementation, output:

* Migration number used (e.g., "020")
* List of files created:
  * migrations/NNN_description.sql
  * migrations/NNN_backfill_description.py (if applicable)
  * migrations/NNN_run_migration.py (if applicable)
* Changes made to init_db.py:
  * New function name: create_<name>
  * Location in init_database() call sequence
* Brief description of what the migration does
* Any notes or assumptions made during implementation

## Example reference

For a complete example of a complex migration, refer to:
* migrations/019_add_sentence_count.sql
* migrations/019_backfill_sentence_count.py
* migrations/019_run_migration.py
* The corresponding updates in src/vulcanlab/data/init_db.py (create_vector_indexes function)

## Critical architectural notes

From patterns.md:

1. **Core Module Independence**: src/vulcanlab must NOT import FastAPI or HTTP-specific code
2. **Session Management**: Pass database sessions as arguments, never create them inside functions
3. **Database Patterns**:
   * Use SQLAlchemy declarative models from src/vulcanlab/data/models
   * Use text() wrapper for raw SQL
   * Always use IF NOT EXISTS / IF EXISTS for idempotency
4. **Ownership**: Transfer function/sequence ownership to app_user after creation
5. **Fresh Install Priority**: init_db.py is the source of truth for fresh installs; migrations are only for existing databases
