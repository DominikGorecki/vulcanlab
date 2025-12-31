#!/usr/bin/env python3
"""
Dump the complete schema from a PostgreSQL database for comparison.

This script extracts:
- All enum types with their values
- All tables with columns and their types
- All indexes
- All triggers and functions
- All constraints

Usage:
    python scripts/dump_db_schema.py > schema_dump.txt
"""

import sys
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


def dump_enums(conn):
    """Dump all enum types."""
    print("=" * 80)
    print("ENUM TYPES")
    print("=" * 80)

    result = conn.execute(text("""
        SELECT
            t.typname as enum_name,
            array_agg(e.enumlabel ORDER BY e.enumsortorder) as enum_values
        FROM pg_type t
        JOIN pg_enum e ON t.oid = e.enumtypid
        JOIN pg_catalog.pg_namespace n ON n.oid = t.typnamespace
        WHERE n.nspname = 'public'
        GROUP BY t.typname
        ORDER BY t.typname
    """))

    for row in result:
        print(f"\nEnum: {row.enum_name}")
        print(f"  Values: {', '.join(row.enum_values)}")


def dump_tables(conn):
    """Dump all tables with their columns."""
    print("\n" + "=" * 80)
    print("TABLES")
    print("=" * 80)

    # Get all tables
    result = conn.execute(text("""
        SELECT table_name
        FROM information_schema.tables
        WHERE table_schema = 'public'
        AND table_type = 'BASE TABLE'
        ORDER BY table_name
    """))

    tables = [row.table_name for row in result]

    for table in tables:
        print(f"\n{'─' * 80}")
        print(f"Table: {table}")
        print(f"{'─' * 80}")

        # Get columns
        result = conn.execute(text("""
            SELECT
                column_name,
                data_type,
                udt_name,
                is_nullable,
                column_default
            FROM information_schema.columns
            WHERE table_name = :table
            AND table_schema = 'public'
            ORDER BY ordinal_position
        """), {"table": table})

        print("\nColumns:")
        for row in result:
            nullable = "NULL" if row.is_nullable == "YES" else "NOT NULL"
            default = f" DEFAULT {row.column_default}" if row.column_default else ""
            type_info = row.udt_name if row.data_type == 'USER-DEFINED' else row.data_type
            print(f"  {row.column_name:30} {type_info:30} {nullable:10}{default}")


def dump_indexes(conn):
    """Dump all indexes."""
    print("\n" + "=" * 80)
    print("INDEXES")
    print("=" * 80)

    result = conn.execute(text("""
        SELECT
            schemaname,
            tablename,
            indexname,
            indexdef
        FROM pg_indexes
        WHERE schemaname = 'public'
        ORDER BY tablename, indexname
    """))

    current_table = None
    for row in result:
        if row.tablename != current_table:
            print(f"\n{'─' * 80}")
            print(f"Table: {row.tablename}")
            print(f"{'─' * 80}")
            current_table = row.tablename

        print(f"\n  Index: {row.indexname}")
        print(f"    {row.indexdef}")


def dump_constraints(conn):
    """Dump all constraints."""
    print("\n" + "=" * 80)
    print("CONSTRAINTS")
    print("=" * 80)

    result = conn.execute(text("""
        SELECT
            tc.table_name,
            tc.constraint_name,
            tc.constraint_type,
            CASE
                WHEN tc.constraint_type = 'FOREIGN KEY' THEN
                    (SELECT ccu.table_name || '(' || ccu.column_name || ')'
                     FROM information_schema.constraint_column_usage ccu
                     WHERE ccu.constraint_name = tc.constraint_name
                     LIMIT 1)
                ELSE NULL
            END as references,
            kcu.column_name
        FROM information_schema.table_constraints tc
        LEFT JOIN information_schema.key_column_usage kcu
            ON tc.constraint_name = kcu.constraint_name
            AND tc.table_schema = kcu.table_schema
        WHERE tc.table_schema = 'public'
        AND tc.constraint_type IN ('PRIMARY KEY', 'FOREIGN KEY', 'UNIQUE', 'CHECK')
        ORDER BY tc.table_name, tc.constraint_type, tc.constraint_name
    """))

    current_table = None
    for row in result:
        if row.table_name != current_table:
            print(f"\n{'─' * 80}")
            print(f"Table: {row.table_name}")
            print(f"{'─' * 80}")
            current_table = row.table_name

        refs = f" -> {row.references}" if row.references else ""
        print(f"  {row.constraint_type:15} {row.constraint_name:40} ({row.column_name}){refs}")


def dump_triggers(conn):
    """Dump all triggers and their functions."""
    print("\n" + "=" * 80)
    print("TRIGGERS AND FUNCTIONS")
    print("=" * 80)

    # Get all triggers
    result = conn.execute(text("""
        SELECT
            trigger_schema,
            event_object_table as table_name,
            trigger_name,
            action_statement,
            event_manipulation,
            action_timing
        FROM information_schema.triggers
        WHERE trigger_schema = 'public'
        ORDER BY event_object_table, trigger_name
    """))

    triggers = list(result)

    if triggers:
        print("\nTriggers:")
        current_table = None
        for row in triggers:
            if row.table_name != current_table:
                print(f"\n  Table: {row.table_name}")
                current_table = row.table_name

            print(f"    Trigger: {row.trigger_name}")
            print(f"      Timing: {row.action_timing} {row.event_manipulation}")
            print(f"      Action: {row.action_statement}")

    # Get all functions
    result = conn.execute(text("""
        SELECT
            p.proname as function_name,
            pg_get_functiondef(p.oid) as function_def
        FROM pg_proc p
        JOIN pg_namespace n ON p.pronamespace = n.oid
        WHERE n.nspname = 'public'
        AND p.prokind = 'f'
        ORDER BY p.proname
    """))

    functions = list(result)

    if functions:
        print("\n" + "─" * 80)
        print("Functions:")
        print("─" * 80)
        for row in functions:
            print(f"\n{row.function_name}:")
            print(row.function_def)


def dump_sequences(conn):
    """Dump all sequences."""
    print("\n" + "=" * 80)
    print("SEQUENCES")
    print("=" * 80)

    result = conn.execute(text("""
        SELECT
            schemaname,
            sequencename
        FROM pg_sequences
        WHERE schemaname = 'public'
        ORDER BY sequencename
    """))

    for row in result:
        print(f"  {row.sequencename}")


def main():
    """Main entry point."""
    engine = get_engine()

    print(f"Database Schema Dump for: {DB_CONFIG['db_name']}")
    print(f"Host: {DB_CONFIG['host']}:{DB_CONFIG['port']}")
    print(f"Timestamp: {__import__('datetime').datetime.now()}")

    with engine.connect() as conn:
        dump_enums(conn)
        dump_tables(conn)
        dump_indexes(conn)
        dump_constraints(conn)
        dump_triggers(conn)
        dump_sequences(conn)

    print("\n" + "=" * 80)
    print("DUMP COMPLETE")
    print("=" * 80)


if __name__ == "__main__":
    try:
        main()
    except Exception as e:
        print(f"Error: {e}", file=sys.stderr)
        import traceback
        traceback.print_exc()
        sys.exit(1)
