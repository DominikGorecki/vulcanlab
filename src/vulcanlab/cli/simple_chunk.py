#!/usr/bin/env python3
"""
Standalone CLI tool for chunking sanitized markdown.

Usage:
    python -m vulcanlab.cli.simple_chunk --work-id 123

This tool creates Chunk records from sanitized markdown, extracting all
headings (H1-H5) and their content sections.
"""

import argparse
import logging
import sys

from vulcanlab.simple_conversion.chunk_simple import create_chunks_standalone

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


def main():
    """CLI entry point."""
    parser = argparse.ArgumentParser(
        description='Create chunks from sanitized markdown for simple conversion'
    )
    parser.add_argument(
        '--work-id',
        type=int,
        required=True,
        help='ID of the Work to process (must be sanitized)'
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
        logger.info(f"Creating chunks for work {args.work_id}")

        chunk_count = create_chunks_standalone(args.work_id)

        print(f"\n{'='*60}")
        print(f"Chunking Complete")
        print(f"{'='*60}")
        print(f"Work ID:        {args.work_id}")
        print(f"Chunks Created: {chunk_count}")
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
