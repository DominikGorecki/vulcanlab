"""
Migration runner for migration 010 (breadcrumb refactoring).

This script runs migration 010 which extracts breadcrumbs from chunk content
and stores them in the new heading_breadcrumbs column.

Usage:
    venv\Scripts\python run_migration_010.py
"""

import sys
import importlib.util
from pathlib import Path

from vulcanLab.data.database import engine


# Load migration module directly from file
migration_path = Path(__file__).parent / "migrations" / "010_refactor_heading_breadcrumbs.py"
spec = importlib.util.spec_from_file_location("migration_010", migration_path)
migration_010 = importlib.util.module_from_spec(spec)
spec.loader.exec_module(migration_010)

upgrade = migration_010.upgrade
downgrade = migration_010.downgrade


def main():
    """Run migration 010."""
    print("=" * 80)
    print("Migration 010: Refactor Heading Breadcrumbs")
    print("=" * 80)
    print()

    # Check if user wants to run upgrade or downgrade
    if len(sys.argv) > 1 and sys.argv[1] == "--downgrade":
        print("Running DOWNGRADE (reverting migration)...")
        print()

        try:
            with engine.connect() as connection:
                downgrade(connection)
            print()
            print("✅ Migration 010 downgrade completed successfully!")

        except Exception as e:
            print()
            print(f"❌ ERROR during migration downgrade: {e}")
            import traceback
            traceback.print_exc()
            sys.exit(1)
    else:
        print("Running UPGRADE (applying migration)...")
        print()

        try:
            with engine.connect() as connection:
                upgrade(connection)
            print()
            print("✅ Migration 010 upgrade completed successfully!")

        except Exception as e:
            print()
            print(f"❌ ERROR during migration upgrade: {e}")
            import traceback
            traceback.print_exc()
            sys.exit(1)


if __name__ == "__main__":
    main()
