#!/usr/bin/env python3
"""
Standalone CLI tool for parsing and classifying documents.

Usage:
    python -m vulcanlab.cli.simple_parse_classify --work-id 123

This tool runs the parse & classify step of the simple conversion pipeline,
counting tokens and classifying the document as SMALL or LARGE based on
the configured threshold.
"""

import argparse
import logging
import sys

from vulcanlab.simple_conversion.parse_classify import parse_and_classify_standalone

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


def main():
    """CLI entry point."""
    parser = argparse.ArgumentParser(
        description='Parse and classify document for simple conversion pipeline'
    )
    parser.add_argument(
        '--work-id',
        type=int,
        required=True,
        help='ID of the Work to process'
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
        logger.info(f"Processing work {args.work_id}")

        token_count, classification = parse_and_classify_standalone(args.work_id)

        print(f"\n{'='*60}")
        print(f"Parse & Classify Complete")
        print(f"{'='*60}")
        print(f"Work ID:        {args.work_id}")
        print(f"Token Count:    {token_count:,}")
        print(f"Classification: {classification}")
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
