#!/usr/bin/env python
"""CLI for content-aware chunking.

Usage:
    venv\\Scripts\\python -m vulcanlab.chunking.content_chunking_cli <work_id> [options]

Examples:
    # Create content chunks for work ID 1
    venv\\Scripts\\python -m vulcanlab.chunking.content_chunking_cli 1

    # With verbose output
    venv\\Scripts\\python -m vulcanlab.chunking.content_chunking_cli 1 -v

Options:
    -v, --verbose    Print progress and validation information

Prerequisites:
    Work must have 'sanitized' in files metadata:
    - Run apply_title_changes_cli to create sanitized markdown
    - Run chunk_headings_cli to create heading chunks (for parent relationships)
"""

import argparse
import sys

from vulcanlab.chunking.content_chunking import chunk_content
from vulcanlab.data.database import get_session
from vulcanlab.data.models import Work
from vulcanlab.sanitization.extract_titles import HashMismatchError


def main():
    """Main entry point for content chunking CLI."""
    parser = argparse.ArgumentParser(
        description="Create content-aware chunks from a work's sanitized markdown"
    )
    parser.add_argument(
        "work_id",
        type=int,
        help="ID of the work in the database"
    )
    parser.add_argument(
        "-v", "--verbose",
        action="store_true",
        help="Print detailed progress information"
    )
    parser.add_argument(
        "--min-words",
        type=int,
        default=50,
        help="Minimum word count for chunks (default: 50)"
    )

    args = parser.parse_args()

    try:
        # Pre-check: Validate work exists and has required files
        with get_session() as session:
            work = session.query(Work).filter(Work.id == args.work_id).first()

            if not work:
                print(f"Error: Work with ID {args.work_id} not found in database", file=sys.stderr)
                return 1

            if not work.files:
                print(f"Error: Work {args.work_id} has no files metadata", file=sys.stderr)
                return 1

            # Check for required files
            if "sanitized" not in work.files:
                print(f"Error: Work {args.work_id} does not have 'sanitized' in files metadata", file=sys.stderr)
                print("\nAvailable files:", file=sys.stderr)
                for key in work.files.keys():
                    print(f"  - {key}", file=sys.stderr)
                print("\nRun the following command first:", file=sys.stderr)
                print(f"  venv\\Scripts\\python -m vulcanlab.sanitization.apply_title_changes_cli {args.work_id}", file=sys.stderr)
                return 1

        # Create content chunks
        count = chunk_content(args.work_id, verbose=args.verbose, min_chunk_words=args.min_words)
        print(f"Successfully created {count} content chunks for work {args.work_id}")
        if args.min_words != 50:
            print(f"Used minimum word count: {args.min_words}")
        return 0

    except HashMismatchError as e:
        print(f"\nError: File hash mismatch detected!", file=sys.stderr)
        print(f"  Stored hash:  {e.stored_hash}", file=sys.stderr)
        print(f"  Current hash: {e.current_hash}", file=sys.stderr)
        print(f"\nThe file may have been modified since it was added to the database.", file=sys.stderr)
        print(f"\nTo fix this, regenerate the sanitized file:", file=sys.stderr)
        print(f"  venv\\Scripts\\python -m vulcanlab.sanitization.apply_title_changes_cli {args.work_id}", file=sys.stderr)
        return 1
    except ValueError as e:
        print(f"Error: {e}", file=sys.stderr)
        return 1
    except FileNotFoundError as e:
        print(f"Error: {e}", file=sys.stderr)
        return 1
    except Exception as e:
        print(f"Unexpected error: {e}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    sys.exit(main())
