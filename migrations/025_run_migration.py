"""
Migration runner for migration 025 (heading_breadcrumbs backfill).
"""

import sys
import importlib.util
from pathlib import Path

from vulcanlab.data.database import engine


# Load migration module directly from file
migration_path = Path(__file__).parent / "025_backfill_heading_breadcrumbs.py"
spec = importlib.util.spec_from_file_location("migration_025", migration_path)
migration_025 = importlib.util.module_from_spec(spec)
spec.loader.exec_module(migration_025)

upgrade = migration_025.upgrade
downgrade = migration_025.downgrade


def main():
    """Run migration 025."""
    print("=" * 80)
    print("Migration 025: Backfill heading_breadcrumbs for All Chunks")
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
            print("✅ Migration 025 downgrade completed successfully!")

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
            print("✅ Migration 025 upgrade completed successfully!")

        except Exception as e:
            print()
            print(f"❌ ERROR during migration upgrade: {e}")
            import traceback
            traceback.print_exc()
            sys.exit(1)


if __name__ == "__main__":
    main()

