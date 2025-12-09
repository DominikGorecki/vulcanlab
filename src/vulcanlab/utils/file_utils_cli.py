"""
CLI for file utility operations.

Usage:
    python -m vulcanlab.utils.file_utils_cli hash <file>
    python -m vulcanlab.utils.file_utils_cli readonly <file>
    python -m vulcanlab.utils.file_utils_cli writable <file>
    python -m vulcanlab.utils.file_utils_cli check <file>
"""

import argparse
import sys
from pathlib import Path

from vulcanlab.utils.file_utils import (
    compute_file_hash,
    set_file_readonly,
    set_file_writable,
    is_file_readonly,
)


def main() -> int:
    """
    Main entry point for the command-line interface.

    Returns:
        Exit code (0 for success, 1 for error).
    """
    parser = argparse.ArgumentParser(
        description="File utility operations.",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  %(prog)s hash document.md           # Compute SHA-256 hash
  %(prog)s readonly document.md       # Set file to read-only
  %(prog)s writable document.md       # Set file to writable
  %(prog)s check document.md          # Check if file is read-only
        """
    )

    subparsers = parser.add_subparsers(dest="command", help="Available commands")

    # hash command
    hash_parser = subparsers.add_parser("hash", help="Compute SHA-256 hash of a file")
    hash_parser.add_argument("file", type=str, help="Path to the file")

    # readonly command
    readonly_parser = subparsers.add_parser("readonly", help="Set file to read-only")
    readonly_parser.add_argument("file", type=str, help="Path to the file")

    # writable command
    writable_parser = subparsers.add_parser("writable", help="Set file to writable")
    writable_parser.add_argument("file", type=str, help="Path to the file")

    # check command
    check_parser = subparsers.add_parser("check", help="Check if file is read-only")
    check_parser.add_argument("file", type=str, help="Path to the file")

    args = parser.parse_args()

    if not args.command:
        parser.print_help()
        return 1

    try:
        file_path = Path(args.file)

        if args.command == "hash":
            hash_value = compute_file_hash(file_path)
            print(hash_value)

        elif args.command == "readonly":
            set_file_readonly(file_path)
            print(f"Set to read-only: {file_path}")

        elif args.command == "writable":
            set_file_writable(file_path)
            print(f"Set to writable: {file_path}")

        elif args.command == "check":
            is_readonly = is_file_readonly(file_path)
            status = "read-only" if is_readonly else "writable"
            print(f"{file_path}: {status}")

        return 0

    except FileNotFoundError as e:
        print(f"Error: {e}", file=sys.stderr)
        return 1
    except Exception as e:
        print(f"Error: {e}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    sys.exit(main())
