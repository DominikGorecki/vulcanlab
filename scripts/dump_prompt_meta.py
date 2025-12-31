#!/usr/bin/env python3
"""
Dump prompt_meta table from the working database.

This script extracts variable definitions for each template.

Usage:
    python scripts/dump_prompt_meta.py
"""

import sys
import json
from sqlalchemy import create_engine, text

# Database connection info
DB_CONFIG = {
    "admin_user": "postgres",
    "admin_password": "postgres",
    "host": "127.0.0.1",
    "port": 5432,
    "db_name": "psych_rag_test"
}

def get_engine():
    """Create database engine."""
    db_url = (
        f"postgresql+psycopg://{DB_CONFIG['admin_user']}:"
        f"{DB_CONFIG['admin_password']}"
        f"@{DB_CONFIG['host']}:"
        f"{DB_CONFIG['port']}/{DB_CONFIG['db_name']}"
    )
    return create_engine(db_url)


def dump_prompt_meta():
    """Dump all prompt_meta records."""
    engine = get_engine()

    print("=" * 80)
    print("Prompt Meta Data (Variable Definitions)")
    print("=" * 80)
    print()

    with engine.connect() as conn:
        result = conn.execute(text("""
            SELECT
                id,
                function_tag,
                variables,
                created_at,
                updated_at
            FROM prompt_meta
            ORDER BY function_tag
        """))

        records = list(result)

        if not records:
            print("No prompt_meta records found!")
            return []

        print(f"Found {len(records)} prompt_meta records\n")

        meta_data = []
        for record in records:
            print(f"{'─' * 80}")
            print(f"Function Tag: {record.function_tag}")
            print(f"{'─' * 80}")
            print(f"  ID: {record.id}")
            print(f"  Variables: {json.dumps(record.variables, indent=2)}")
            print(f"  Created: {record.created_at}")
            print(f"  Updated: {record.updated_at}")
            print()

            meta_data.append({
                "function_tag": record.function_tag,
                "variables": record.variables
            })

        print("=" * 80)
        print(f"Total: {len(records)} records")
        print("=" * 80)

        return meta_data


if __name__ == "__main__":
    try:
        dump_prompt_meta()
    except Exception as e:
        print(f"Error: {e}", file=sys.stderr)
        import traceback
        traceback.print_exc()
        sys.exit(1)
