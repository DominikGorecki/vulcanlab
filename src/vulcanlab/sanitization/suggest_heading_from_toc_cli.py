"""DEPRECATE
CLI for suggesting heading hierarchy changes based on TOC titles.

Usage:
    python -m vulcanlab.sanitization.suggest_heading_from_toc_cli <titles_file> <toc_titles_file>

Examples:
    python -m vulcanlab.sanitization.suggest_heading_from_toc_cli output/book.titles.md output/book.toc_titles.md
"""

import argparse
import sys
from pathlib import Path

from .suggest_heading_from_toc import suggest_heading_from_toc


def main() -> int:
    """Main entry point for the CLI."""
    parser = argparse.ArgumentParser(
        description="Suggest heading hierarchy changes based on TOC titles"
    )
    parser.add_argument(
        "titles_file",
        type=Path,
        help="Path to the .titles.md file to analyze"
    )
    parser.add_argument(
        "toc_titles_file",
        type=Path,
        help="Path to the .toc_titles.md file (authoritative TOC)"
    )
    parser.add_argument(
        "-o", "--output",
        type=Path,
        default=None,
        help="Output file path (default: output/<stem>.title_changes.md)"
    )

    args = parser.parse_args()

    try:
        output_path = suggest_heading_from_toc(
            args.titles_file,
            args.toc_titles_file,
            args.output
        )
        print(f"Heading changes saved to: {output_path}")
        return 0
    except FileNotFoundError as e:
        print(f"Error: {e}", file=sys.stderr)
        return 1
    except ValueError as e:
        print(f"Error: {e}", file=sys.stderr)
        return 1
    except Exception as e:
        print(f"Unexpected error: {e}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    sys.exit(main())
