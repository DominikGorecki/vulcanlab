#!/usr/bin/env python
"""CLI for vectorizing chunks.

Usage:
    python -m vulcanlab.vectorization.vect_chunks_cli <work_id> [--limit N] [--verbose]

Examples:
    python -m vulcanlab.vectorization.vect_chunks_cli 1 --limit 10
    python -m vulcanlab.vectorization.vect_chunks_cli 1 --verbose
    python -m vulcanlab.vectorization.vect_chunks_cli 1  # Interactive mode
"""

import argparse
import sys

from vulcanlab.vectorization.vect_chunks import (
    DEFAULT_BATCH_SIZE,
    get_eligible_chunks_count,
    vectorize_chunks,
)


def main():
    """Main entry point for vectorization CLI."""
    parser = argparse.ArgumentParser(
        description="Create vector embeddings for chunks"
    )
    parser.add_argument(
        "work_id",
        type=int,
        help="ID of the work in the database"
    )
    parser.add_argument(
        "--limit",
        type=int,
        default=None,
        help="Maximum number of chunks to vectorize"
    )
    parser.add_argument(
        "-v", "--verbose",
        action="store_true",
        help="Print detailed progress information"
    )
    parser.add_argument(
        "--batch-size",
        type=int,
        default=DEFAULT_BATCH_SIZE,
        help=f"Number of chunks per API batch (default: {DEFAULT_BATCH_SIZE})"
    )

    args = parser.parse_args()

    try:
        # Get count of eligible chunks
        eligible_count = get_eligible_chunks_count(args.work_id)

        if eligible_count == 0:
            print(f"No eligible chunks found for work {args.work_id}")
            return 0

        # Determine limit
        limit = args.limit

        if limit is None:
            # Interactive mode
            print(f"Found {eligible_count} chunks eligible for vectorization.")
            print("Enter Y to process all, N to cancel, or a number to set limit:")

            response = input("> ").strip()

            if response.upper() == 'N':
                print("Cancelled.")
                return 0
            elif response.upper() == 'Y':
                limit = None  # Process all
            else:
                try:
                    limit = int(response)
                    if limit <= 0:
                        print("Limit must be positive. Cancelled.")
                        return 1
                except ValueError:
                    print(f"Invalid input: {response}. Cancelled.")
                    return 1

        # Run vectorization
        result = vectorize_chunks(
            args.work_id,
            limit=limit,
            batch_size=args.batch_size,
            verbose=args.verbose
        )

        # Print summary
        print(f"\nVectorization complete for work {args.work_id}:")
        print(f"  Total eligible: {result.total_eligible}")
        print(f"  Processed: {result.processed}")
        print(f"  Success: {result.success}")
        print(f"  Failed: {result.failed}")

        if result.errors:
            print("\nErrors:")
            for chunk_id, error in result.errors[:10]:  # Show first 10 errors
                print(f"  Chunk {chunk_id}: {error}")
            if len(result.errors) > 10:
                print(f"  ... and {len(result.errors) - 10} more errors")

        return 0 if result.failed == 0 else 1

    except ValueError as e:
        print(f"Error: {e}", file=sys.stderr)
        return 1
    except KeyboardInterrupt:
        print("\nInterrupted.")
        return 1
    except Exception as e:
        print(f"Unexpected error: {e}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    sys.exit(main())
