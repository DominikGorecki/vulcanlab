---
description: Debug and inspect the PostgreSQL database for troubleshooting. Read-only by default - no schema or data changes unless explicitly requested.
-------------------------------------------

You are helping debug database issues by inspecting schema, data, and configuration.

## Hard requirements

* **READ-ONLY by default**: Do NOT make any schema changes (ALTER TABLE, DROP, CREATE) or data modifications (INSERT, UPDATE, DELETE) unless explicitly asked by the user.
* If a fix requires schema/data changes, you MUST ask for permission first and explain what change is needed and why.
* Always use the virtual environment Python for database access.

## Environment setup

* **Python venv location**: `/home/dardawk/python/vulcanlab/venv`
* **Run Python commands via**: `venv/bin/python -c "..."`
* **Database config file**: `vulcanlab.config.json` in project root
  * Contains: `database.host`, `database.port`, `database.db_name`, `database.admin_user`
* **Credentials**: Ask the user for passwords if not provided. Common pattern:
  * Admin user: `postgres` with password from user
  * App user: defined in config with password from user

## Database connection pattern

Use SQLAlchemy with inline Python for quick queries:

```bash
venv/bin/python -c "
from sqlalchemy import create_engine, text

# Read config from vulcanlab.config.json or use values directly
engine = create_engine('postgresql+psycopg://postgres:<PASSWORD>@127.0.0.1:5432/<DB_NAME>')

with engine.connect() as conn:
    result = conn.execute(text('SELECT ...'))
    for row in result:
        print(row)
"
```

## Common debugging queries

### Check table schema
```python
result = conn.execute(text('''
    SELECT column_name, data_type, udt_name, is_nullable
    FROM information_schema.columns
    WHERE table_name = '<TABLE_NAME>'
    ORDER BY ordinal_position
'''))
```

### Check vector column dimensions (pgvector)
```python
result = conn.execute(text('''
    SELECT pg_catalog.format_type(atttypid, atttypmod) as data_type
    FROM pg_attribute a
    JOIN pg_class t ON a.attrelid = t.oid
    WHERE t.relname = 'chunks' AND a.attname = 'embedding'
'''))
```

### Count records and check data presence
```python
result = conn.execute(text('SELECT COUNT(*) FROM <TABLE> WHERE <CONDITION>'))
count = result.scalar()
```

### Check foreign key relationships
```python
result = conn.execute(text('''
    SELECT id, parent_id, <other_columns>
    FROM <TABLE>
    WHERE <CONDITION>
    LIMIT 20
'''))
```

### Group by for data distribution
```python
result = conn.execute(text('''
    SELECT <column>, COUNT(*) as cnt
    FROM <TABLE>
    GROUP BY <column>
    ORDER BY <column>
'''))
```

## Existing debug scripts

Reference scripts in `/scripts` folder for patterns:

* `scripts/dump_db_schema.py` - Dumps complete schema (enums, tables, indexes, constraints, triggers, sequences)
* Pattern: Creates SQLAlchemy engine, uses `text()` for raw SQL, iterates results

## Using application code for context

When debugging application-level issues, you can import application models:

```bash
venv/bin/python -c "
import sys
sys.path.insert(0, 'src')

from vulcanlab.data.database import get_session
from vulcanlab.data.models.<model> import <Model>
from sqlalchemy import select

with get_session() as session:
    # Use ORM queries
    result = session.execute(select(<Model>).where(...))
    ...
"
```

## Workflow

1. **Understand the issue**: What table/data is involved? What's the expected vs actual behavior?
2. **Read config**: Check `vulcanlab.config.json` for database connection details
3. **Inspect schema**: Verify table structure, column types, constraints
4. **Query data**: Check actual data state, counts, relationships
5. **Compare databases**: If user has multiple DBs (e.g., backup config), compare schemas/data
6. **Report findings**: Summarize what you found, potential causes, and recommended fixes
7. **If fix needed**: Ask permission before making any changes

## Important notes

* Always use parameterized queries when user input is involved
* For large result sets, use LIMIT to avoid overwhelming output
* When checking embeddings/vectors, verify dimension matches between DB schema and embedding model
* Check `vector_status` column on chunks table to understand vectorization state
