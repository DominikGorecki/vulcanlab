#!/usr/bin/env python
""" DEPRECATING
Extract bibliographic info and TOC from a markdown file.

Usage:
    venv\\Scripts\\python -m vulcanlab.chunking.extract_bib_cli <file> [options]

Examples:
    # Extract metadata from file
    venv\\Scripts\\python -m vulcanlab.chunking.extract_bib_cli doc.md

    # Preview first 2000 characters without LLM call
    venv\\Scripts\\python -m vulcanlab.chunking.extract_bib_cli doc.md --preview --chars 2000

    # Preview first 100 lines without LLM call
    venv\\Scripts\\python -m vulcanlab.chunking.extract_bib_cli doc.md --preview --lines 100

    # Use custom character limit
    venv\\Scripts\\python -m vulcanlab.chunking.extract_bib_cli doc.md --chars 1500

    # Use custom line limit (overrides --chars)
    venv\\Scripts\\python -m vulcanlab.chunking.extract_bib_cli doc.md --lines 150

Options:
    --chars N    Characters to extract (default: 1000)
    --lines N    Lines to extract (overrides --chars)
    --preview    Show extracted text only, no LLM call
"""

import argparse
import sys
from pathlib import Path

from vulcanlab.chunking import extract_metadata, EXTRACT_CHARS


def main():
    parser = argparse.ArgumentParser(
        description="Extract bibliographic information and table of contents from a markdown file."
    )
    parser.add_argument(
        "file",
        type=Path,
        help="Path to the markdown file to analyze"
    )
    parser.add_argument(
        "--chars",
        type=int,
        default=EXTRACT_CHARS,
        help=f"Number of characters to extract from the beginning (default: {EXTRACT_CHARS})"
    )
    parser.add_argument(
        "--lines",
        type=int,
        default=None,
        help="Number of lines to extract from the beginning (overrides --chars)"
    )
    parser.add_argument(
        "--preview",
        action="store_true",
        help="Only preview the extracted text without calling the LLM"
    )

    args = parser.parse_args()

    if not args.file.exists():
        print(f"Error: File not found: {args.file}", file=sys.stderr)
        sys.exit(1)

    if not args.file.is_file():
        print(f"Error: Not a file: {args.file}", file=sys.stderr)
        sys.exit(1)

    # Read the markdown file
    try:
        markdown_text = args.file.read_text(encoding="utf-8")
    except Exception as e:
        print(f"Error reading file: {e}", file=sys.stderr)
        sys.exit(1)

    # Determine text sample based on lines or chars
    if args.lines is not None:
        text_lines = markdown_text.split('\n')
        text_sample = '\n'.join(text_lines[:args.lines])
        extract_desc = f"{args.lines} lines"
        total_units = len(text_lines)
        unit_name = "lines"
    else:
        text_sample = markdown_text[:args.chars]
        extract_desc = f"{args.chars} characters"
        total_units = len(markdown_text)
        unit_name = "characters"

    # Preview mode - just show the extracted text
    if args.preview:
        print(f"Preview of first {extract_desc} from {args.file.name}:")
        print("=" * 60)
        print(text_sample)
        print("=" * 60)
        if args.lines is not None:
            print(f"\nTotal lines shown: {min(len(text_lines), args.lines)}")
        else:
            print(f"\nTotal characters shown: {min(len(markdown_text), args.chars)}")
        print(f"Total file length: {total_units} {unit_name}")
        sys.exit(0)

    # Extract metadata
    print(f"Extracting metadata from first {extract_desc} of {args.file.name}...")
    print()

    result = extract_metadata(markdown_text, chars=args.chars, lines=args.lines)

    # Print bibliographic information
    print("=" * 60)
    print("BIBLIOGRAPHIC INFORMATION")
    print("=" * 60)
    bib = result.bibliographic
    print(f"Title:            {bib.title or 'Not found'}")
    print(f"Authors:          {', '.join(bib.authors) if bib.authors else 'Not found'}")
    print(f"Publication Date: {bib.publication_date or 'Not found'}")
    print(f"Publisher:        {bib.publisher or 'Not found'}")
    print(f"ISBN:             {bib.isbn or 'Not found'}")
    print(f"Edition:          {bib.edition or 'Not found'}")
    print()

    # Print table of contents
    print("=" * 60)
    print("TABLE OF CONTENTS")
    print("=" * 60)
    if result.toc.entries:
        for entry in result.toc.entries:
            indent = "  " * (entry.level - 1)
            print(f"{indent}H{entry.level}: {entry.title}")
    else:
        print("No table of contents found")
    print()


if __name__ == "__main__":
    main()
