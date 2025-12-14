#!/usr/bin/env python3
"""
Standalone CLI tool for sanitizing large documents.

Usage:
    python -m vulcanlab.cli.simple_sanitize_large --work-id 123

This tool runs the large document sanitization step using condensed
heading analysis instead of processing the full document.
"""

import argparse
import logging
import sys

from vulcanlab.simple_conversion.sanitize_large import sanitize_large_document_standalone

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


def main():
    """CLI entry point."""
    parser = argparse.ArgumentParser(
        description='Sanitize large document using condensed heading analysis'
    )
    parser.add_argument(
        '--work-id',
        type=int,
        required=True,
        help='ID of the Work to process (must be classified as LARGE)'
    )
    parser.add_argument(
        '--verbose',
        '-v',
        action='store_true',
        help='Enable verbose logging'
    )

    args = parser.parse_args()

    if args.verbose:
        logging.getLogger().setLevel(logging.DEBUG)

    try:
        logger.info(f"Sanitizing large document for work {args.work_id}")

        heading_count, condensed_chars = sanitize_large_document_standalone(args.work_id)

        print(f"\n{'='*60}")
        print(f"Large Document Sanitization Complete")
        print(f"{'='*60}")
        print(f"Work ID:               {args.work_id}")
        print(f"Headings Analyzed:     {heading_count}")
        print(f"Condensed Size:        {condensed_chars:,} chars")
        print(f"{'='*60}\n")

        sys.exit(0)

    except ValueError as e:
        logger.error(f"Validation error: {e}")
        sys.exit(1)
    except Exception as e:
        logger.error(f"Unexpected error: {e}", exc_info=True)
        sys.exit(2)


if __name__ == '__main__':
    main()
