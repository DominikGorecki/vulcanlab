"""
Migration runner for migration 015 (convert paths to filenames).

This script runs migration 015 which converts absolute paths to relative filenames
in the Works table, enabling environment portability.

Usage:
    venv/bin/python migrations/015_run_migration.py
"""

import sys
import importlib.util
from pathlib import Path

from vulcanlab.data.database import engine


# Load migration module directly from file
migration_path = Path(__file__).parent / "015_convert_paths_to_filenames.py"
spec = importlib.util.spec_from_file_location("migration_015", migration_path)
migration_015 = importlib.util.module_from_spec(spec)
spec.loader.exec_module(migration_015)

upgrade = migration_015.upgrade


def main():
    """Run migration 015."""
    print("=" * 80)
    print("Migration 015: Convert Absolute Paths to Filenames")
    print("=" * 80)
    print()
    print("Running UPGRADE (applying migration)...")
    print()

    try:
        with engine.connect() as connection:
            upgrade(connection)
        print()
        print("✅ Migration 015 upgrade completed successfully!")

    except Exception as e:
        print()
        print(f"❌ ERROR during migration upgrade: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)


if __name__ == "__main__":
    main()
