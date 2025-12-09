"""
CLI for IO folder data management.

Usage:
    python -m vulcanlab.config.io_folder_data_cli
"""

import argparse
import sys

from vulcanlab.config.io_folder_data import get_io_folder_data


def main() -> int:
    """
    Main entry point for the command-line interface.

    Returns:
        Exit code (0 for success, 1 for error).
    """
    parser = argparse.ArgumentParser(
        description="Scan input/output folders and show unprocessed files.",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  %(prog)s                # Show all unprocessed files
        """
    )

    parser.parse_args()

    try:
        # Get IO folder data
        data = get_io_folder_data()

        # Display input files
        print("\n" + "=" * 70)
        print("INPUT FILES (Unprocessed)")
        print("=" * 70)

        if data.input_files:
            for filename in data.input_files:
                print(f"  {filename}")
        else:
            print("  (no unprocessed input files)")

        print()

        # Display output files with their variants
        print("=" * 70)
        print("OUTPUT FILES (Unprocessed)")
        print("=" * 70)

        if data.processed_files:
            for pf in data.processed_files:
                # Format: <file>|<id>|.pdf|.md|.style.md
                id_str = str(pf.io_file_id) if pf.io_file_id else "no-id"
                variants_str = "|".join(pf.variants)
                print(f"  {pf.base_name}|{id_str}|{variants_str}")
        else:
            print("  (no unprocessed output files)")

        print("=" * 70 + "\n")

        return 0

    except Exception as e:
        print(f"Error: {e}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    sys.exit(main())
