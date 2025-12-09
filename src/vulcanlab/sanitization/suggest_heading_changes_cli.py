"""CLI for suggesting heading hierarchy changes from works in the database.

Analyze markdown headings using AI and suggest corrections based on
the table of contents stored in the database. This version works with Work IDs.

Usage:
    venv\\Scripts\\python -m vulcanlab.sanitization.suggest_heading_changes_cli <work_id> [options]

Examples:
    # Suggest changes for work ID 5 (auto-select if only one pair exists)
    venv\\Scripts\\python -m vulcanlab.sanitization.suggest_heading_changes_cli 5

    # Specify which source to use
    venv\\Scripts\\python -m vulcanlab.sanitization.suggest_heading_changes_cli 5 --source original_markdown
    venv\\Scripts\\python -m vulcanlab.sanitization.suggest_heading_changes_cli 5 --source sanitized

    # Use full LLM model instead of light
    venv\\Scripts\\python -m vulcanlab.sanitization.suggest_heading_changes_cli 5 --full-llm

    # Force analysis even if hashes don't match
    venv\\Scripts\\python -m vulcanlab.sanitization.suggest_heading_changes_cli 5 --force

    # Verbose output
    venv\\Scripts\\python -m vulcanlab.sanitization.suggest_heading_changes_cli 5 -v

Options:
    work_id                 Database ID of the work
    --source SOURCE         Which file to use: 'original_markdown' or 'sanitized' (auto-select if only one pair exists)
    --full-llm              Use full LLM model instead of light (more expensive but better)
    --force                 Proceed even if file hashes don't match database
    -v, --verbose           Print detailed progress messages
"""

import argparse
import sys
from pathlib import Path

from vulcanlab.data.database import get_session
from vulcanlab.data.models.work import Work
from .suggest_heading_changes import suggest_heading_changes_from_work
from .extract_titles import HashMismatchError


def main() -> int:
    """Main entry point for the CLI."""
    parser = argparse.ArgumentParser(
        description="Suggest heading changes from a work's markdown file by Work ID",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  %(prog)s 5                                    # Auto-select source if only one pair exists
  %(prog)s 5 --source original_markdown         # Use original markdown
  %(prog)s 5 --source sanitized                 # Use sanitized markdown
  %(prog)s 5 --full-llm                         # Use full LLM model
  %(prog)s 5 --force                            # Force despite hash mismatch
  %(prog)s 5 -v                                 # Verbose output

This tool analyzes headings and suggests corrections using AI,
then updates the database with the new title_changes file metadata.
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
        help="Which file to analyze (auto-select if not specified)"
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
        # Load work from database to check available file pairs
        with get_session() as session:
            work = session.query(Work).filter(Work.id == args.work_id).first()

            if not work:
                print(f"Error: Work with ID {args.work_id} not found in database", file=sys.stderr)
                return 1

            if not work.files:
                print(f"Error: Work {args.work_id} has no files metadata", file=sys.stderr)
                return 1

            # Determine which complete pairs are available (markdown + titles)
            available_pairs = []

            # Check original_markdown + titles
            if "original_markdown" in work.files and "titles" in work.files:
                available_pairs.append("original_markdown")

            # Check sanitized + sanitized_titles
            if "sanitized" in work.files and "sanitized_titles" in work.files:
                available_pairs.append("sanitized")

            if not available_pairs:
                print(f"Error: Work {args.work_id} has no complete markdown + titles pairs", file=sys.stderr)
                print("Available files:", file=sys.stderr)
                for key in work.files.keys():
                    print(f"  - {key}", file=sys.stderr)
                print("\nRun extract_titles_from_work first to generate titles.", file=sys.stderr)
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
                print("Multiple markdown + titles pairs available:")
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

        # Analyze headings
        if args.verbose:
            model_desc = "full" if args.full_llm else "light"
            print(f"\nAnalyzing headings from work {args.work_id} ({source_key}) using {model_desc} model...")

        try:
            output_path = suggest_heading_changes_from_work(
                work_id=args.work_id,
                source_key=source_key,
                use_full_model=args.full_llm,
                force=args.force,
                verbose=args.verbose
            )

            print(f"\nSuccess!")
            print(f"  Work ID: {args.work_id}")
            print(f"  Source: {source_key}")
            print(f"  Model: {'FULL' if args.full_llm else 'LIGHT'}")
            print(f"  Title changes saved to: {output_path}")

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
                output_path = suggest_heading_changes_from_work(
                    work_id=args.work_id,
                    source_key=source_key,
                    use_full_model=args.full_llm,
                    force=True,
                    verbose=args.verbose
                )
                print(f"Title changes saved to: {output_path}")
                return 0
            else:
                # Ask user if they want to continue
                try:
                    choice = input("\nContinue anyway? (y/n): ").strip().lower()
                    if choice == 'y':
                        output_path = suggest_heading_changes_from_work(
                            work_id=args.work_id,
                            source_key=source_key,
                            use_full_model=args.full_llm,
                            force=True,
                            verbose=args.verbose
                        )
                        print(f"\nSuccess! Title changes saved to: {output_path}")
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
