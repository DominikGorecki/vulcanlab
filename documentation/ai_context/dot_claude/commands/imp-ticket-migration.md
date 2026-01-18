---

description: Implement database schema changes or data backfills.
argument-hint: [path/to/work-ticket.md]
--------------------------------------------

You implement database changes following VulcanLab's "Single-Source Schema" pattern: all schema changes (tables, columns, indexes, enums) are defined in the code (via `src/vulcanlab/data/schema/`) and orchestrated by `init_db.py`. This ensures they apply to both fresh installs and existing databases. Manual migration scripts in `migrations/` are ONLY used for data backfills or transformations.

* $1 = path to a work ticket file, typically `documentation/work/<ticket-name>.md`.

## Hard requirements

* You MUST read the ticket file ($1) fully before doing anything else.
* You MUST read `documentation/patterns.md` fully before implementing.
* You MUST define all schema changes (CREATE TABLE, ALTER TABLE ADD COLUMN, etc.) in the appropriate module within `src/vulcanlab/data/schema/`.
* You MUST use idempotent SQL patterns (e.g., `IF NOT EXISTS`, `IF EXISTS`) to ensure `init_db.py` is safe to run on existing databases.
* You MUST NOT include destructive schema changes or delete existing data in `init_db.py`.
* You MUST ONLY create files in the `migrations/` folder if a data backfill or transformation is required for existing data.
* You MUST update the SQLAlchemy models in `src/vulcanlab/data/models/` to match any schema changes.
* You MUST follow the three-tier architecture: Core Module (`src/vulcanlab`) is framework-independent.
* Use plain output. Do NOT use emojis or icon-like characters.

## Step 1: Validate input

* If $1 is empty, ask for the ticket path and STOP.
* If $1 does not exist or is not a Markdown file, ask for a valid ticket path and STOP.

## Step 2: Load context

1. Read the ticket ($1) fully.
2. Read `documentation/patterns.md` fully to understand:
   * Single-source-of-truth schema approach (Section 5.2)
   * Database patterns (SQLAlchemy ORM, lowercase enums)
   * Modular `init_db` structure (Section 5.1)
3. Explore `src/vulcanlab/data/schema/` to identify the correct module for your changes:
   * `enums.py`: PostgreSQL enum types
   * `tables.py`: Core ORM tables
   * `indexes.py`: Vector, fulltext, and history indexes
   * `triggers.py`: Common triggers (updated_at)
   * `specialized_tables.py`: Feature-specific tables (research, collections, etc.)

## Step 3: Determine implementation strategy

Based on the ticket requirements, determine what needs to be updated:

### 1. Schema Changes (Required for new fields/tables)
* Add/Modify SQL in the appropriate module in `src/vulcanlab/data/schema/*.py`.
* Update Python models in `src/vulcanlab/data/models/*.py`.
* **Pattern**: Always use idempotent SQL (e.g., `ALTER TABLE ... ADD COLUMN IF NOT EXISTS`).

### 2. Data Backfill (Required ONLY for existing data)
* If the change requires populating new columns with computed values from existing records or transforming existing data.
* Create: `migrations/NNN_backfill_description.sql` or `migrations/NNN_backfill_description.py`.

### 3. Seeding (Required for new default data)
* Update `src/vulcanlab/data/seeding/` or `src/vulcanlab/data/seed_data/`.

## Step 4: Implement Schema Changes

Modify the relevant files in `src/vulcanlab/data/schema/`. Use `engine.connect()` and `text()` from SQLAlchemy.

**Example: Adding a column in `specialized_tables.py`**
```python
def create_research_tables(verbose: bool = False) -> None:
    # ... existing code ...
    with engine.connect() as conn:
        conn.execute(text("""
            ALTER TABLE research_sessions ADD COLUMN IF NOT EXISTS new_metadata JSONB;
        """))
        conn.commit()
```

**CRITICAL**: You MUST also update the corresponding SQLAlchemy model in `src/vulcanlab/data/models/`.

## Step 5: Implement Data Backfill (If needed)

If a backfill is required:
1. Scan the `migrations/` folder for the next migration number (NNN).
2. Create `migrations/NNN_backfill_description.sql` (or `.py` and a runner if logic is complex).
3. Follow the backfill patterns defined in `documentation/patterns.md` (batch processing, progress logging).

## Step 6: Implementation Checklist

1. [ ] Update Schema Module (`src/vulcanlab/data/schema/*.py`) with idempotent SQL.
2. [ ] Update SQLAlchemy Model (`src/vulcanlab/data/models/*.py`).
3. [ ] If data backfill needed, create `migrations/NNN_backfill_*.sql` or `.py`.
4. [ ] If default data needed, update `seeding/` or `seed_data/`.

## Step 7: Report back

After implementation, output:
* Files modified in `src/vulcanlab/data/schema/`.
* Models updated in `src/vulcanlab/data/models/`.
* Any backfill scripts created in `migrations/`.
* Summary of changes.
* Instructions for the user: "Run `python -m vulcanlab.data.init_db -v` to apply schema changes."
* If a backfill script was created, provide instructions to run it.
