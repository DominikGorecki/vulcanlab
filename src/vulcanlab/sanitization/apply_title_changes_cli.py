"""CLI for applying title changes to markdown documents from works in the database.

Apply heading changes using AI-suggested corrections stored in title_changes files.
This version works with Work IDs.

Usage:
    venv\\Scripts\\python -m vulcanlab.sanitization.apply_title_changes_cli <work_id> [options]

Examples:
    # Apply changes for work ID 5 (auto-select if only one pair exists)
    venv\\Scripts\\python -m vulcanlab.sanitization.apply_title_changes_cli 5

    # Specify which source to use
    venv\\Scripts\\python -m vulcanlab.sanitization.apply_title_changes_cli 5 --source original_markdown
    venv\\Scripts\\python -m vulcanlab.sanitization.apply_title_changes_cli 5 --source sanitized

    # Force application even if hashes don't match
    venv\\Scripts\\python -m vulcanlab.sanitization.apply_title_changes_cli 5 --force

    # Verbose output
    venv\\Scripts\\python -m vulcanlab.sanitization.apply_title_changes_cli 5 -v

Options:
    work_id                 Database ID of the work
    --source SOURCE         Which file to use: 'original_markdown' or 'sanitized' (auto-select if only one pair exists)
    --force                 Proceed even if file hashes don't match database
    -v, --verbose           Print detailed progress messages
"""

import argparse
import sys
from pathlib import Path

from vulcanlab.data.database import get_session
from vulcanlab.data.models.work import Work
from .apply_title_changes import apply_title_changes_from_work
from .extract_titles import HashMismatchError


def main() -> int:
    """Main entry point for the CLI."""
    parser = argparse.ArgumentParser(
        description="Apply title changes from a work's files by Work ID",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  %(prog)s 5                                    # Auto-select source if only one pair exists
  %(prog)s 5 --source original_markdown         # Use original markdown
  %(prog)s 5 --source sanitized                 # Use sanitized markdown
  %(prog)s 5 --force                            # Force despite hash mismatch
  %(prog)s 5 -v                                 # Verbose output

This tool applies heading changes and creates a sanitized markdown file,
then updates the database with the new sanitized file metadata.
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
        help="Which file to use (auto-select if not specified)"
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
        # Load work from database to check available file pairs
        with get_session() as session:
            work = session.query(Work).filter(Work.id == args.work_id).first()

            if not work:
                print(f"Error: Work with ID {args.work_id} not found in database", file=sys.stderr)
                return 1

            if not work.files:
                print(f"Error: Work {args.work_id} has no files metadata", file=sys.stderr)
                return 1

            # Determine which complete pairs are available (markdown + title_changes)
            available_pairs = []

            # Check original_markdown + title_changes
            if "original_markdown" in work.files and "title_changes" in work.files:
                available_pairs.append("original_markdown")

            # Check sanitized + sanitized_title_changes
            if "sanitized" in work.files and "sanitized_title_changes" in work.files:
                available_pairs.append("sanitized")

            if not available_pairs:
                print(f"Error: Work {args.work_id} has no complete markdown + title_changes pairs", file=sys.stderr)
                print("Available files:", file=sys.stderr)
                for key in work.files.keys():
                    print(f"  - {key}", file=sys.stderr)
                print("\nRun suggest_heading_changes_from_work first to generate title_changes.", file=sys.stderr)
                return 1

            # Determine source to use
            if args.source:
                # User specified source
                source_key = args.source
                if source_key not in available_pairs:
                    print(
                        f"Error: Work {args.work_id} does not have complete '{source_key}' pair",
                        file=sys.stderr
                    )
                    print(f"Available pairs: {', '.join(available_pairs)}", file=sys.stderr)
                    return 1
            elif len(available_pairs) == 1:
                # Only one option, use it automatically
                source_key = available_pairs[0]
                if args.verbose:
                    print(f"Auto-selected source: {source_key}")
            else:
                # Multiple options, prompt user
                print("Multiple markdown + title_changes pairs available:")
                for i, src in enumerate(available_pairs, start=1):
                    print(f"  {i}. {src}")

                while True:
                    try:
                        choice = input(f"Select source (1-{len(available_pairs)}): ").strip()
                        choice_idx = int(choice) - 1

                        if 0 <= choice_idx < len(available_pairs):
                            source_key = available_pairs[choice_idx]
                            break
                        else:
                            print(f"Invalid choice. Please enter a number between 1 and {len(available_pairs)}")
                    except ValueError:
                        print("Invalid input. Please enter a number")
                    except KeyboardInterrupt:
                        print("\n\nOperation cancelled by user.", file=sys.stderr)
                        return 1

        # Check if sanitized file already exists and prompt for overwrite
        with get_session() as session:
            work = session.query(Work).filter(Work.id == args.work_id).first()

            # Determine output path
            if source_key == "original_markdown":
                markdown_path = Path(work.files["original_markdown"]["path"])
                output_path = markdown_path.parent / f"{markdown_path.stem}.sanitized.md"
            else:  # sanitized
                output_path = Path(work.files["sanitized"]["path"])

            if output_path.exists() and not args.force:
                print(f"\nWarning: Sanitized file already exists: {output_path}", file=sys.stderr)
                try:
                    choice = input("Overwrite existing file? (y/n): ").strip().lower()
                    if choice != 'y':
                        print("Operation cancelled.", file=sys.stderr)
                        return 0
                except KeyboardInterrupt:
                    print("\n\nOperation cancelled by user.", file=sys.stderr)
                    return 1

        # Apply title changes
        if args.verbose:
            print(f"\nApplying title changes from work {args.work_id} ({source_key})...")

        try:
            output_path = apply_title_changes_from_work(
                work_id=args.work_id,
                source_key=source_key,
                force=args.force,
                verbose=args.verbose
            )

            print(f"\nSuccess!")
            print(f"  Work ID: {args.work_id}")
            print(f"  Source: {source_key}")
            print(f"  Sanitized file saved to: {output_path}")
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
                output_path = apply_title_changes_from_work(
                    work_id=args.work_id,
                    source_key=source_key,
                    force=True,
                    verbose=args.verbose
                )
                print(f"Sanitized file saved to: {output_path}")
                return 0
            else:
                # Ask user if they want to continue
                try:
                    choice = input("\nContinue anyway? (y/n): ").strip().lower()
                    if choice == 'y':
                        output_path = apply_title_changes_from_work(
                            work_id=args.work_id,
                            source_key=source_key,
                            force=True,
                            verbose=args.verbose
                        )
                        print(f"\nSuccess! Sanitized file saved to: {output_path}")
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
