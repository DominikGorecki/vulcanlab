"""CLI for LLM-based document processing.

Process markdown documents using LLM to extract bibliography, sanitize headings,
and generate table of contents.

Usage:
    venv\\Scripts\\python -m vulcanlab.chunking.llm_processor_cli <input_file> [options]

Examples:
    # Process a document
    venv\\Scripts\\python -m vulcanlab.chunking.llm_processor_cli book.md

    # Process a large file (>2000 lines)
    venv\\Scripts\\python -m vulcanlab.chunking.llm_processor_cli large_book.md --force

Options:
    input_file          Path to the markdown file to process
    --force             Process files larger than 2000 lines
    -v, --verbose       Print progress information
"""

import argparse
import sys
from pathlib import Path

from .llm_processor import process_with_llm


def main() -> int:
    """Main entry point for the CLI."""
    parser = argparse.ArgumentParser(
        description="Process markdown documents using LLM for bibliography, TOC, and sanitization"
    )
    parser.add_argument(
        "input_file",
        type=Path,
        help="Path to the markdown file to process"
    )
    parser.add_argument(
        "--force",
        action="store_true",
        help="Process files larger than 2000 lines"
    )
    parser.add_argument(
        "-v", "--verbose",
        action="store_true",
        help="Print progress information"
    )

    args = parser.parse_args()

    try:
        result = process_with_llm(
            args.input_file,
            force=args.force,
            verbose=args.verbose
        )

        print(f"\n=== Processing Complete ===")
        print(f"Title: {result.bibliographic.title or 'N/A'}")
        print(f"Authors: {', '.join(result.bibliographic.authors) if result.bibliographic.authors else 'N/A'}")
        print(f"Year: {result.bibliographic.year or 'N/A'}")
        print(f"Publisher: {result.bibliographic.publisher or 'N/A'}")
        print(f"TOC entries: {len(result.toc)}")

        if result.toc:
            print(f"\n=== Table of Contents ===")
            for entry in result.toc[:20]:
                indent = "  " * (entry.level - 1)
                print(f"{indent}{entry.title}")
            if len(result.toc) > 20:
                print(f"  ... and {len(result.toc) - 20} more entries")

        return 0

    except FileNotFoundError as e:
        print(f"Error: {e}", file=sys.stderr)
        return 1
    except ValueError as e:
        print(f"Error: {e}", file=sys.stderr)
        return 1
    except Exception as e:
        print(f"Processing failed: {e}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    sys.exit(main())
