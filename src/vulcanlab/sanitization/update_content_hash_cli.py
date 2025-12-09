"""CLI for updating content hash after validation.

Validates file integrity and updates the content hash in the database.

Usage:
    python -m vulcanlab.sanitization.update_content_hash_cli <work_id> [--verbose]

Examples:
    python -m vulcanlab.sanitization.update_content_hash_cli 1
    python -m vulcanlab.sanitization.update_content_hash_cli 1 --verbose
"""

import argparse
import sys

from .update_content_hash import update_content_hash


def main() -> int:
    """Main entry point for the CLI."""
    parser = argparse.ArgumentParser(
        description="Validate files and update content hash for a work"
    )

    parser.add_argument(
        "work_id",
        type=int,
        help="ID of the work in the database"
    )

    parser.add_argument(
        "-v", "--verbose",
        action="store_true",
        help="Print progress information"
    )

    args = parser.parse_args()

    try:
        success = update_content_hash(args.work_id, verbose=args.verbose)
        if success:
            return 0
        else:
            print("Validation failed - hash not updated", file=sys.stderr)
            return 1
    except ValueError as e:
        print(f"Error: {e}", file=sys.stderr)
        return 1
    except Exception as e:
        print(f"Unexpected error: {e}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    sys.exit(main())
