#!/usr/bin/env python3
"""
Standalone CLI tool for sanitizing small documents.

Usage:
    python -m vulcanlab.cli.simple_sanitize_small --work-id 123

This tool runs the small document sanitization step of the simple conversion
pipeline, sending the full markdown to an LLM for sanitization.
"""

import argparse
import logging
import sys

from vulcanlab.simple_conversion.sanitize_small import sanitize_small_document_standalone

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


def main():
    """CLI entry point."""
    parser = argparse.ArgumentParser(
        description='Sanitize small document for simple conversion pipeline'
    )
    parser.add_argument(
        '--work-id',
        type=int,
        required=True,
        help='ID of the Work to process (must be classified as SMALL)'
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
        logger.info(f"Sanitizing small document for work {args.work_id}")

        mod_count = sanitize_small_document_standalone(args.work_id)

        print(f"\n{'='*60}")
        print(f"Small Document Sanitization Complete")
        print(f"{'='*60}")
        print(f"Work ID:              {args.work_id}")
        print(f"Heading Modifications: {mod_count}")
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
