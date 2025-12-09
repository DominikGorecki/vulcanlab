"""
CLI for applying string mappings to sanitize markdown documents.

Usage:
    python -m vulcanlab.sanitization.san_map_cli <markdown_file> <csv_file> <work_id>

Examples:
    python -m vulcanlab.sanitization.san_map_cli output/book.md output/book.san_mapping.csv 1
"""

import argparse
import sys
from pathlib import Path

from .san_map import preview_san_mapping, apply_san_mapping


def main() -> int:
    """Main entry point for the CLI."""
    parser = argparse.ArgumentParser(
        description="Apply string mappings from CSV to sanitize markdown"
    )
    parser.add_argument(
        "markdown_file",
        type=Path,
        help="Path to the markdown file to sanitize"
    )
    parser.add_argument(
        "csv_file",
        type=Path,
        help="Path to the CSV mapping file with 'old' and 'new' columns"
    )
    parser.add_argument(
        "work_id",
        type=int,
        help="ID of the Work record in the database"
    )

    args = parser.parse_args()

    try:
        # Get preview
        preview = preview_san_mapping(args.markdown_file, args.csv_file)

        if not preview['counts']:
            print("No matches found for any mappings.")
            return 0

        # Display preview
        print(f"\n=== Preview of {preview['total_replacements']} replacements ===\n")
        print(f"{'Old Value':<30} {'New Value':<30} {'Count'}")
        print("-" * 70)

        for old_val, new_val in preview['mappings']:
            if old_val in preview['counts']:
                count = preview['counts'][old_val]
                # Truncate long strings for display
                old_display = old_val[:27] + "..." if len(old_val) > 30 else old_val
                new_display = new_val[:27] + "..." if len(new_val) > 30 else new_val
                print(f"{old_display:<30} {new_display:<30} {count}")
            else:
                # Show mappings with 0 matches for debugging
                old_display = old_val[:27] + "..." if len(old_val) > 30 else old_val
                new_display = new_val[:27] + "..." if len(new_val) > 30 else new_val
                print(f"{old_display:<30} {new_display:<30} 0 (no matches)")

        print(f"\nTotal: {preview['total_replacements']} replacements")

        # Prompt for confirmation
        print("\nApply these replacements? [Y/N]: ", end="")
        response = input().strip().upper()

        if response != "Y":
            print("Replacements not applied.")
            return 0

        # Apply mappings
        output_path = apply_san_mapping(
            args.markdown_file,
            args.csv_file,
            args.work_id
        )
        print(f"\nReplacements applied to: {output_path}")
        print("Database updated with new content hash.")

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
