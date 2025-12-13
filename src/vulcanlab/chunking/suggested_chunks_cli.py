"""CLI for suggesting which document sections to vectorize from works in the database.

Analyze markdown headings using AI to determine which sections should be chunked
and stored in the vector database. This version works with Work IDs.

Usage:
    venv\\Scripts\\python -m vulcanlab.chunking.suggested_chunks_cli <work_id> [options]

Examples:
    # Suggest chunks for work ID 5
    venv\\Scripts\\python -m vulcanlab.chunking.suggested_chunks_cli 5

    # Use full LLM model instead of light
    venv\\Scripts\\python -m vulcanlab.chunking.suggested_chunks_cli 5 --full-llm

    # Force analysis even if hashes don't match
    venv\\Scripts\\python -m vulcanlab.chunking.suggested_chunks_cli 5 --force

    # Verbose output
    venv\\Scripts\\python -m vulcanlab.chunking.suggested_chunks_cli 5 -v

Options:
    work_id                 Database ID of the work
    --full-llm              Use full LLM model instead of light (more expensive but better)
    --force                 Proceed even if file hashes don't match database
    -v, --verbose           Print detailed progress messages
"""

import argparse
import sys
from pathlib import Path

from vulcanlab.data.database import get_session
from vulcanlab.data.models.work import Work
from vulcanlab.chunking.suggested_chunks import suggest_chunks_from_work
from vulcanlab.sanitization.extract_titles import HashMismatchError
from vulcanlab.utils.file_utils import get_path_resolver


# Initialize path resolver
resolver = get_path_resolver()


def main() -> int:
    """Main entry point for the CLI."""
    parser = argparse.ArgumentParser(
        description="Suggest vectorization sections from a work's sanitized markdown by Work ID",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  %(prog)s 5                    # Suggest chunks for work ID 5
  %(prog)s 5 --full-llm          # Use full LLM model
  %(prog)s 5 --force             # Force despite hash mismatch
  %(prog)s 5 -v                  # Verbose output

This tool analyzes document headings and suggests which sections to vectorize,
then updates the database with the new vec_suggestions file metadata.
        """
    )

    parser.add_argument(
        "work_id",
        type=int,
        help="Database ID of the work"
    )

    parser.add_argument(
        "--full-llm",
        action="store_true",
        help="Use full LLM model instead of light (more expensive but better)"
    )

    parser.add_argument(
        "--force",
        action="store_true",
        help="Proceed even if file hashes don't match database"
    )

    parser.add_argument(
        "-v", "--verbose",
        action="store_true",
        help="Print detailed progress messages"
    )

    args = parser.parse_args()

    try:
        # Load work from database to check if sanitized exists
        with get_session() as session:
            work = session.query(Work).filter(Work.id == args.work_id).first()

            if not work:
                print(f"Error: Work with ID {args.work_id} not found in database", file=sys.stderr)
                return 1

            if not work.files:
                print(f"Error: Work {args.work_id} has no files metadata", file=sys.stderr)
                return 1

            # Check if sanitized file exists
            if "sanitized" not in work.files:
                print(f"Error: Work {args.work_id} does not have 'sanitized' in files metadata", file=sys.stderr)
                print("Available files:", file=sys.stderr)
                for key in work.files.keys():
                    print(f"  - {key}", file=sys.stderr)
                print("\nRun apply_title_changes_from_work first to create sanitized markdown.", file=sys.stderr)
                return 1

            # Check if output file already exists and prompt for overwrite
            sanitized_path = resolver.resolve_work_path(work, "sanitized")
            output_path = sanitized_path.parent / f"{sanitized_path.stem}.vec_sugg.md"

            if output_path.exists() and not args.force:
                print(f"\nWarning: Vectorization suggestions file already exists: {output_path}", file=sys.stderr)
                try:
                    choice = input("Overwrite existing file? (y/n): ").strip().lower()
                    if choice != 'y':
                        print("Operation cancelled.", file=sys.stderr)
                        return 0
                except KeyboardInterrupt:
                    print("\n\nOperation cancelled by user.", file=sys.stderr)
                    return 1

        # Suggest chunks
        if args.verbose:
            model_desc = "full" if args.full_llm else "light"
            print(f"\nAnalyzing headings from work {args.work_id} using {model_desc} model...")

        try:
            output_path = suggest_chunks_from_work(
                work_id=args.work_id,
                use_full_model=args.full_llm,
                force=args.force,
                verbose=args.verbose
            )

            print(f"\nSuccess!")
            print(f"  Work ID: {args.work_id}")
            print(f"  Model: {'FULL' if args.full_llm else 'LIGHT'}")
            print(f"  Vectorization suggestions saved to: {output_path}")
            print(f"  File set to read-only")

            return 0

        except HashMismatchError as e:
            # Hash mismatch - prompt user
            print(f"\nWarning: File hash mismatch detected!", file=sys.stderr)
            print(f"  {str(e)}", file=sys.stderr)
            print(f"\nOne or more files may have been modified since they were added to the database.", file=sys.stderr)

            if args.force:
                # This shouldn't happen since force=True should prevent the exception
                # But handle it just in case
                print("Proceeding with --force flag...", file=sys.stderr)
                output_path = suggest_chunks_from_work(
                    work_id=args.work_id,
                    use_full_model=args.full_llm,
                    force=True,
                    verbose=args.verbose
                )
                print(f"Vectorization suggestions saved to: {output_path}")
                return 0
            else:
                # Ask user if they want to continue
                try:
                    choice = input("\nContinue anyway? (y/n): ").strip().lower()
                    if choice == 'y':
                        output_path = suggest_chunks_from_work(
                            work_id=args.work_id,
                            use_full_model=args.full_llm,
                            force=True,
                            verbose=args.verbose
                        )
                        print(f"\nSuccess! Vectorization suggestions saved to: {output_path}")
                        return 0
                    else:
                        print("Operation cancelled.", file=sys.stderr)
                        return 1
                except KeyboardInterrupt:
                    print("\n\nOperation cancelled by user.", file=sys.stderr)
                    return 1

    except ValueError as e:
        print(f"Error: {e}", file=sys.stderr)
        return 1
    except FileNotFoundError as e:
        print(f"Error: {e}", file=sys.stderr)
        return 1
    except KeyboardInterrupt:
        print("\n\nOperation cancelled by user.", file=sys.stderr)
        return 1
    except Exception as e:
        print(f"Unexpected error: {e}", file=sys.stderr)
        if args.verbose:
            import traceback
            traceback.print_exc()
        return 1


if __name__ == "__main__":
    sys.exit(main())

