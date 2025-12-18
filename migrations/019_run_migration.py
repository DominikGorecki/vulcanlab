"""
Migration runner for migration 019 (sentence_count backfill).

This script runs migration 019 which populates the sentence_count column
for all existing chunks by re-parsing sanitized markdown content.

Usage:
    python migrations/019_run_migration.py              # Run upgrade
    python migrations/019_run_migration.py --downgrade  # Run downgrade
"""

import sys
import importlib.util
from pathlib import Path

from vulcanlab.data.database import engine


# Load migration module directly from file
migration_path = Path(__file__).parent / "019_backfill_sentence_count.py"
spec = importlib.util.spec_from_file_location("migration_019", migration_path)
migration_019 = importlib.util.module_from_spec(spec)
spec.loader.exec_module(migration_019)

upgrade = migration_019.upgrade
downgrade = migration_019.downgrade


def main():
    """Run migration 019."""
    print("=" * 80)
    print("Migration 019: Backfill sentence_count for Existing Chunks")
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
            print("✅ Migration 019 downgrade completed successfully!")

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
            print("✅ Migration 019 upgrade completed successfully!")

        except Exception as e:
            print()
            print(f"❌ ERROR during migration upgrade: {e}")
            import traceback
            traceback.print_exc()
            sys.exit(1)


if __name__ == "__main__":
    main()
