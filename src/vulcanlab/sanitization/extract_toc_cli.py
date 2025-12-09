"""
CLI for extracting table of contents from markdown files.

Usage:
    python -m vulcanlab.sanitization.extract_toc_cli document.md
    python -m vulcanlab.sanitization.extract_toc_cli document.md --chars 5000 -v
"""

import argparse
import sys
from pathlib import Path

from vulcanlab.sanitization.extract_toc import extract_table_of_contents
from vulcanlab.data.database import SessionLocal
from vulcanlab.data.models import Work


def main() -> int:
    """
    Main entry point for the command-line interface.

    Returns:
        Exit code (0 for success, 1 for error).
    """
    parser = argparse.ArgumentParser(
        description="Extract table of contents from markdown files.",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  %(prog)s document.md                    # Extract and prompt to save
  %(prog)s document.md --chars 5000       # Use more context
  %(prog)s document.md --lines 200        # Use first 200 lines
  %(prog)s document.md -v                 # Verbose output
        """
    )

    parser.add_argument(
        "input_file",
        type=str,
        help="Path to the input Markdown file"
    )

    parser.add_argument(
        "--chars",
        type=int,
        default=None,
        help="Number of characters to extract from the beginning for TOC extraction"
    )

    parser.add_argument(
        "--lines",
        type=int,
        default=None,
        help="Number of lines to extract from the beginning (overrides --chars)"
    )

    parser.add_argument(
        "-v", "--verbose",
        action="store_true",
        help="Print progress information"
    )

    args = parser.parse_args()

    try:
        input_path = Path(args.input_file)

        if not input_path.exists():
            print(f"Error: File not found: {input_path}", file=sys.stderr)
            return 1

        # Extract table of contents
        if args.verbose:
            print("Extracting table of contents...")

        toc = extract_table_of_contents(
            markdown_path=args.input_file,
            chars=args.chars,
            lines=args.lines,
        )

        # Convert TOC entries to JSON-serializable format
        toc_json = [
            {"level": entry.level, "title": entry.title}
            for entry in toc.entries
        ]

        # Display extracted TOC
        print(f"\n=== Table of Contents ({len(toc_json)} entries) ===")
        for entry in toc_json[:20]:  # Show first 20 entries
            indent = "  " * (entry["level"] - 1)
            print(f"{indent}{entry['title']}")
        if len(toc_json) > 20:
            print(f"  ... and {len(toc_json) - 20} more entries")

        if not toc_json:
            print("No TOC entries found.")
            return 0

        # Prompt user to save
        print("\nSave to database? Enter Work ID (or N to cancel): ", end="")
        response = input().strip()

        if response.upper() == "N":
            print("Not saved.")
            return 0

        # Parse work ID
        try:
            work_id = int(response)
        except ValueError:
            print(f"Error: Invalid Work ID: {response}", file=sys.stderr)
            return 1

        # Update the Work record with TOC
        with SessionLocal() as session:
            work = session.query(Work).filter(Work.id == work_id).first()
            if not work:
                print(f"Error: Work with ID {work_id} not found", file=sys.stderr)
                return 1

            work.toc = toc_json
            session.commit()
            print(f"Updated TOC for: {work.title} (id={work_id})")

        return 0

    except FileNotFoundError as e:
        print(f"Error: {e}", file=sys.stderr)
        return 1
    except ValueError as e:
        print(f"Error: {e}", file=sys.stderr)
        return 1
    except Exception as e:
        print(f"Extraction failed: {e}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    sys.exit(main())
