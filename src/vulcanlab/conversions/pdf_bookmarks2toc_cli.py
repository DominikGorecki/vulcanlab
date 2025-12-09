"""
CLI for PDF Bookmarks to Table of Contents Extractor.

Usage:
    venv\\Scripts\\python -m vulcanlab.conversions.pdf_bookmarks2toc_cli input.pdf
    venv\\Scripts\\python -m vulcanlab.conversions.pdf_bookmarks2toc_cli input.pdf -o custom_toc.md -v
"""

import argparse
import sys

from vulcanlab.conversions.pdf_bookmarks2toc import extract_bookmarks_to_toc


def main() -> int:
    """
    Main entry point for the command-line interface.

    Returns:
        Exit code (0 for success, 1 for error).
    """
    parser = argparse.ArgumentParser(
        description="Extract PDF bookmarks to hierarchical markdown TOC.",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  %(prog)s document.pdf                    # Output to document.toc_titles.md
  %(prog)s document.pdf -o custom.md       # Output to custom.md
  %(prog)s document.pdf -v                 # Verbose output
        """
    )

    parser.add_argument(
        "pdf_path",
        type=str,
        help="Path to the input PDF file"
    )

    parser.add_argument(
        "-o", "--output",
        type=str,
        default=None,
        help="Path for the output markdown file (default: <pdf_stem>.toc_titles.md)"
    )

    parser.add_argument(
        "-v", "--verbose",
        action="store_true",
        help="Print progress information"
    )

    args = parser.parse_args()

    try:
        result = extract_bookmarks_to_toc(
            pdf_path=args.pdf_path,
            output_path=args.output,
            verbose=args.verbose,
        )

        if not result:
            print("No bookmarks found in PDF", file=sys.stderr)
            return 1

        if args.verbose:
            print("\nGenerated TOC:")
            print(result)

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
