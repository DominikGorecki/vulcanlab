"""
CLI for creating new work entries in the database.

Interactive command-line interface for inserting bibliographic metadata
into the works table.

Usage:
    python -m vulcanlab.conversions.new_work__cli <markdown_file>
    python -m vulcanlab.conversions.new_work__cli output/document.md

Example:
    $ python -m vulcanlab.sanitization.new_work__cli output/cognitive.md
    Title: Cognitive Psychology and Cognitive Neuroscience
    Authors [optional]: John Smith, Jane Doe
    Publication Year (YYYY) [optional]: 2025
    Publisher [optional]: Academic Press
    ISBN [optional]: 978-0123456789
    Edition [optional]: 3rd Edition

    Successfully created work:
      ID: 1
      Title: Cognitive Psychology and Cognitive Neuroscience
      Authors: John Smith, Jane Doe
      Year: 2025
      Markdown: output/cognitive.md
      Hash: a1b2c3d4...
"""

import argparse
import sys
from pathlib import Path

from .new_work import create_new_work, DuplicateWorkError


def prompt_user(field_name: str, required: bool = False) -> str:
    """
    Prompt user for input with optional field indication.

    Args:
        field_name: Name of the field to prompt for.
        required: If True, field is required and cannot be empty.

    Returns:
        User input string (empty string if optional and skipped).
    """
    suffix = "" if required else " [optional]"
    prompt = f"{field_name}{suffix}: "

    while True:
        value = input(prompt).strip()

        if required and not value:
            print(f"Error: {field_name} is required. Please enter a value.")
            continue

        return value


def main() -> int:
    """
    Main entry point for the CLI.

    Returns:
        Exit code (0 for success, 1 for error).
    """
    parser = argparse.ArgumentParser(
        description="Create a new work entry in the database.",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  %(prog)s output/document.md
  %(prog)s output/cognitive_psychology.md

This tool will interactively prompt you for bibliographic information
and insert a new work entry into the database with the provided markdown file.

Required fields:
  - Title
  - Markdown file path (provided as argument)

Optional fields:
  - Authors
  - Publication Year (must be 4-digit year format: YYYY)
  - Publisher
  - ISBN
  - Edition
        """
    )

    parser.add_argument(
        "markdown_file",
        type=str,
        help="Path to the markdown file"
    )

    parser.add_argument(
        "--no-duplicate-check",
        action="store_true",
        help="Skip checking for duplicate works based on content hash"
    )

    parser.add_argument(
        "-v", "--verbose",
        action="store_true",
        help="Print verbose messages (warnings for TOC issues)"
    )

    args = parser.parse_args()

    try:
        # Validate markdown file
        markdown_path = Path(args.markdown_file)

        if not markdown_path.exists():
            print(f"Error: Markdown file not found: {markdown_path}", file=sys.stderr)
            return 1

        if not markdown_path.is_file():
            print(f"Error: Path is not a file: {markdown_path}", file=sys.stderr)
            return 1

        print(f"\nCreating new work entry for: {markdown_path}")
        print("Please provide the following information:\n")

        # Prompt for required fields
        title = prompt_user("Title", required=True)

        # Prompt for optional fields
        authors = prompt_user("Authors")
        authors = authors if authors else None

        # Year with validation
        year_str = prompt_user("Publication Year (YYYY)")
        year = None
        if year_str:
            try:
                year = int(year_str)
                if year < 1000 or year > 9999:
                    print("Warning: Year should be in YYYY format (4 digits). Continuing anyway...")
            except ValueError:
                print(f"Error: Invalid year format: '{year_str}'. Must be an integer.", file=sys.stderr)
                return 1

        publisher = prompt_user("Publisher")
        publisher = publisher if publisher else None

        isbn = prompt_user("ISBN")
        isbn = isbn if isbn else None

        edition = prompt_user("Edition")
        edition = edition if edition else None

        # Create the work
        print("\nCreating work entry...")

        work = create_new_work(
            title=title,
            markdown_path=markdown_path,
            authors=authors,
            year=year,
            publisher=publisher,
            isbn=isbn,
            edition=edition,
            check_duplicates=not args.no_duplicate_check,
            verbose=args.verbose
        )

        # Print success message with details
        print("\nSuccessfully created work:")
        print(f"  ID: {work.id}")
        print(f"  Title: {work.title}")
        if work.authors:
            print(f"  Authors: {work.authors}")
        if work.year:
            print(f"  Year: {work.year}")
        if work.publisher:
            print(f"  Publisher: {work.publisher}")
        if work.isbn:
            print(f"  ISBN: {work.isbn}")
        if work.abstract:  # Edition stored in abstract
            print(f"  Edition: {work.abstract}")
        print(f"  Markdown: {work.markdown_path}")
        if work.toc:
            print(f"  TOC Entries: {len(work.toc)}")
        if work.files:
            print(f"  Files Discovered: {len(work.files)}")
        print(f"  Hash: {work.content_hash[:16]}...")

        return 0

    except DuplicateWorkError as e:
        print(f"\nError: {e}", file=sys.stderr)
        print("Use --no-duplicate-check to force insertion.", file=sys.stderr)
        return 1

    except FileNotFoundError as e:
        print(f"Error: {e}", file=sys.stderr)
        return 1

    except ValueError as e:
        print(f"Error: {e}", file=sys.stderr)
        return 1

    except KeyboardInterrupt:
        print("\n\nOperation cancelled by user.", file=sys.stderr)
        return 1

    except Exception as e:
        print(f"Error: {e}", file=sys.stderr)
        import traceback
        traceback.print_exc()
        return 1


if __name__ == "__main__":
    sys.exit(main())
