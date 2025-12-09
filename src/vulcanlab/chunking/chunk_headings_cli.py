"""CLI for chunking document headings into database.

Usage:
    venv\\Scripts\\python -m vulcanlab.chunking.chunk_headings_cli <work_id> [options]

Examples:
    # Chunk headings for work ID 1
    venv\\Scripts\\python -m vulcanlab.chunking.chunk_headings_cli 1

    # With verbose output
    venv\\Scripts\\python -m vulcanlab.chunking.chunk_headings_cli 1 -v

Options:
    -v, --verbose    Print progress and validation information

Prerequisites:
    Work must have 'sanitized' and 'vec_suggestions' in files metadata:
    - Run apply_title_changes_cli to create sanitized markdown
    - Run suggested_chunks_cli to create vectorization suggestions
"""

import argparse
import sys

from vulcanlab.chunking.chunk_headings import chunk_headings
from vulcanlab.data.database import get_session
from vulcanlab.data.models import Work
from vulcanlab.sanitization.extract_titles import HashMismatchError


def main() -> int:
    """Main entry point for the CLI."""
    parser = argparse.ArgumentParser(
        description="Chunk document headings into database"
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
            missing_files = []
            if "sanitized" not in work.files:
                missing_files.append("sanitized")
            if "vec_suggestions" not in work.files:
                missing_files.append("vec_suggestions")

            if missing_files:
                print(f"Error: Work {args.work_id} is missing required files in metadata:", file=sys.stderr)
                for f in missing_files:
                    print(f"  - {f}", file=sys.stderr)
                print("\nAvailable files:", file=sys.stderr)
                for key in work.files.keys():
                    print(f"  - {key}", file=sys.stderr)
                print("\nRun the following commands first:", file=sys.stderr)
                if "sanitized" in missing_files:
                    print(f"  venv\\Scripts\\python -m vulcanlab.sanitization.apply_title_changes_cli {args.work_id}", file=sys.stderr)
                if "vec_suggestions" in missing_files:
                    print(f"  venv\\Scripts\\python -m vulcanlab.chunking.suggested_chunks_cli {args.work_id}", file=sys.stderr)
                return 1

        # Chunk headings
        count = chunk_headings(args.work_id, verbose=args.verbose)
        print(f"Successfully created {count} chunks for work {args.work_id}")
        return 0

    except HashMismatchError as e:
        print(f"\nError: File hash mismatch detected!", file=sys.stderr)
        print(f"  Stored hash:  {e.stored_hash}", file=sys.stderr)
        print(f"  Current hash: {e.current_hash}", file=sys.stderr)
        print(f"\nThe file may have been modified since it was added to the database.", file=sys.stderr)
        print(f"Line numbers in vec_suggestions must match the sanitized markdown exactly.", file=sys.stderr)
        print(f"\nTo fix this, regenerate the pipeline files:", file=sys.stderr)
        print(f"  venv\\Scripts\\python -m vulcanlab.sanitization.apply_title_changes_cli {args.work_id}", file=sys.stderr)
        print(f"  venv\\Scripts\\python -m vulcanlab.chunking.suggested_chunks_cli {args.work_id}", file=sys.stderr)
        return 1
    except ValueError as e:
        print(f"Error: {e}", file=sys.stderr)
        return 1
    except FileNotFoundError as e:
        print(f"Error: {e}", file=sys.stderr)
        return 1
    except Exception as e:
        print(f"Error: {e}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    sys.exit(main())
