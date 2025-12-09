"""CLI for extracting markdown titles from works in the database.

Extract all headings from a work's markdown file and save them with line numbers
for hierarchy analysis. This version works with Work IDs from the database.

Usage:
    venv\\Scripts\\python -m vulcanlab.sanitization.extract_titles_cli <work_id> [options]

Examples:
    # Extract titles from work ID 5 (auto-select if only one markdown file)
    venv\\Scripts\\python -m vulcanlab.sanitization.extract_titles_cli 5

    # Specify which source to use
    venv\\Scripts\\python -m vulcanlab.sanitization.extract_titles_cli 5 --source original_markdown
    venv\\Scripts\\python -m vulcanlab.sanitization.extract_titles_cli 5 --source sanitized

    # Force extraction even if hash doesn't match
    venv\\Scripts\\python -m vulcanlab.sanitization.extract_titles_cli 5 --force

    # Verbose output
    venv\\Scripts\\python -m vulcanlab.sanitization.extract_titles_cli 5 -v

Options:
    work_id                 Database ID of the work
    --source SOURCE         Which file to use: 'original_markdown' or 'sanitized' (auto-select if only one exists)
    --force                 Proceed even if file hash doesn't match database
    -v, --verbose           Print detailed progress messages
"""

import argparse
import sys
from pathlib import Path

from vulcanlab.data.database import get_session
from vulcanlab.data.models.work import Work
from .extract_titles import extract_titles_from_work, HashMismatchError


def main() -> int:
    """Main entry point for the CLI."""
    parser = argparse.ArgumentParser(
        description="Extract titles from a work's markdown file by Work ID",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  %(prog)s 5                                    # Auto-select source if only one exists
  %(prog)s 5 --source original_markdown         # Extract from original markdown
  %(prog)s 5 --source sanitized                 # Extract from sanitized markdown
  %(prog)s 5 --force                            # Force extraction despite hash mismatch
  %(prog)s 5 -v                                 # Verbose output

This tool extracts all headings from a work's markdown file and updates
the database with the new titles file metadata.
        """
    )

    parser.add_argument(
        "work_id",
        type=int,
        help="Database ID of the work"
    )

    parser.add_argument(
        "--source",
        type=str,
        choices=["original_markdown", "sanitized"],
        default=None,
        help="Which file to extract from (auto-select if not specified)"
    )

    parser.add_argument(
        "--force",
        action="store_true",
        help="Proceed even if file hash doesn't match database"
    )

    parser.add_argument(
        "-v", "--verbose",
        action="store_true",
        help="Print detailed progress messages"
    )

    args = parser.parse_args()

    try:
        # Load work from database to check available files
        with get_session() as session:
            work = session.query(Work).filter(Work.id == args.work_id).first()

            if not work:
                print(f"Error: Work with ID {args.work_id} not found in database", file=sys.stderr)
                return 1

            if not work.files:
                print(f"Error: Work {args.work_id} has no files metadata", file=sys.stderr)
                return 1

            # Determine which markdown files are available
            available_sources = []
            if "original_markdown" in work.files:
                available_sources.append("original_markdown")
            if "sanitized" in work.files:
                available_sources.append("sanitized")

            if not available_sources:
                print(f"Error: Work {args.work_id} has no markdown files in metadata", file=sys.stderr)
                return 1

            # Determine source to use
            if args.source:
                # User specified source
                source_key = args.source
                if source_key not in available_sources:
                    print(
                        f"Error: Work {args.work_id} does not have '{source_key}' in files",
                        file=sys.stderr
                    )
                    print(f"Available sources: {', '.join(available_sources)}", file=sys.stderr)
                    return 1
            elif len(available_sources) == 1:
                # Only one option, use it automatically
                source_key = available_sources[0]
                if args.verbose:
                    print(f"Auto-selected source: {source_key}")
            else:
                # Multiple options, prompt user
                print("Multiple markdown files available:")
                for i, src in enumerate(available_sources, start=1):
                    print(f"  {i}. {src}")

                while True:
                    try:
                        choice = input(f"Select source (1-{len(available_sources)}): ").strip()
                        choice_idx = int(choice) - 1

                        if 0 <= choice_idx < len(available_sources):
                            source_key = available_sources[choice_idx]
                            break
                        else:
                            print(f"Invalid choice. Please enter a number between 1 and {len(available_sources)}")
                    except ValueError:
                        print("Invalid input. Please enter a number")
                    except KeyboardInterrupt:
                        print("\n\nOperation cancelled by user.", file=sys.stderr)
                        return 1

        # Extract titles
        if args.verbose:
            print(f"\nExtracting titles from work {args.work_id} ({source_key})...")

        try:
            output_path = extract_titles_from_work(
                work_id=args.work_id,
                source_key=source_key,
                force=args.force,
                verbose=args.verbose
            )

            print(f"\nSuccess!")
            print(f"  Work ID: {args.work_id}")
            print(f"  Source: {source_key}")
            print(f"  Titles saved to: {output_path}")

            return 0

        except HashMismatchError as e:
            # Hash mismatch - prompt user
            print(f"\nWarning: File hash mismatch detected!", file=sys.stderr)
            print(f"  Stored hash:  {e.stored_hash}", file=sys.stderr)
            print(f"  Current hash: {e.current_hash}", file=sys.stderr)
            print(f"\nThe file may have been modified since it was added to the database.", file=sys.stderr)

            if args.force:
                # This shouldn't happen since force=True should prevent the exception
                # But handle it just in case
                print("Proceeding with --force flag...", file=sys.stderr)
                output_path = extract_titles_from_work(
                    work_id=args.work_id,
                    source_key=source_key,
                    force=True,
                    verbose=args.verbose
                )
                print(f"Titles saved to: {output_path}")
                return 0
            else:
                # Ask user if they want to continue
                try:
                    choice = input("\nContinue anyway? (y/n): ").strip().lower()
                    if choice == 'y':
                        output_path = extract_titles_from_work(
                            work_id=args.work_id,
                            source_key=source_key,
                            force=True,
                            verbose=args.verbose
                        )
                        print(f"\nSuccess! Titles saved to: {output_path}")
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
