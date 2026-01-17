"""
Migration runner for migration 030 (fix tabs in content).

Usage:
    python migrations/030_run_migration.py                    # Run upgrade
    python migrations/030_run_migration.py --downgrade        # Run downgrade
    python migrations/030_run_migration.py --chunk-id 123     # Test single chunk
    python migrations/030_run_migration.py --dry-run          # Preview changes
    python migrations/030_run_migration.py --batch-size 1000  # Custom batch size
"""

import sys
import importlib.util
from pathlib import Path

from vulcanlab.data.database import engine


# Load migration module directly from file
migration_path = Path(__file__).parent / "030_fix_tabs_in_content.py"
spec = importlib.util.spec_from_file_location("migration_030", migration_path)
migration_030 = importlib.util.module_from_spec(spec)
spec.loader.exec_module(migration_030)

upgrade = migration_030.upgrade
downgrade = migration_030.downgrade
process_single_chunk = migration_030.process_single_chunk
DEFAULT_BATCH_SIZE = migration_030.DEFAULT_BATCH_SIZE


def main():
    """Run migration 030."""
    import argparse

    parser = argparse.ArgumentParser(
        description="Migration 030: Fix tabs in chunk content"
    )
    parser.add_argument(
        "--downgrade",
        action="store_true",
        help="Run downgrade (rollback) instead of upgrade"
    )
    parser.add_argument(
        "--chunk-id",
        type=int,
        help="Process a single chunk by ID (for testing)"
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Don't make changes, just show what would happen"
    )
    parser.add_argument(
        "--batch-size",
        type=int,
        default=DEFAULT_BATCH_SIZE,
        help=f"Batch size for processing (default: {DEFAULT_BATCH_SIZE})"
    )

    args = parser.parse_args()

    print("=" * 80)
    print("Migration 030: Fix Tabs in Chunk Content")
    print("=" * 80)
    print()

    if args.downgrade:
        print("Running DOWNGRADE...")
        print()
        try:
            with engine.connect() as connection:
                downgrade(connection)
            print()
            print("Migration 030 downgrade completed.")
        except Exception as e:
            print()
            print(f"ERROR during migration downgrade: {e}")
            import traceback
            traceback.print_exc()
            sys.exit(1)

    elif args.chunk_id:
        print(f"Processing single chunk ID: {args.chunk_id}")
        if args.dry_run:
            print("DRY RUN MODE - No changes will be made")
        print()
        try:
            with engine.connect() as connection:
                result = process_single_chunk(
                    connection,
                    args.chunk_id,
                    dry_run=args.dry_run
                )
                print("Result:")
                for key, value in result.items():
                    if key == "tab_ratio":
                        print(f"  {key}: {value:.2%}")
                    else:
                        print(f"  {key}: {value}")
        except Exception as e:
            print()
            print(f"ERROR: {e}")
            import traceback
            traceback.print_exc()
            sys.exit(1)

    else:
        print("Running UPGRADE...")
        if args.dry_run:
            print("DRY RUN MODE - No changes will be made")
        print()
        try:
            with engine.connect() as connection:
                upgrade(
                    connection,
                    batch_size=args.batch_size,
                    dry_run=args.dry_run
                )
            print()
            print("Migration 030 upgrade completed successfully!")
        except Exception as e:
            print()
            print(f"ERROR during migration upgrade: {e}")
            import traceback
            traceback.print_exc()
            sys.exit(1)


if __name__ == "__main__":
    main()
