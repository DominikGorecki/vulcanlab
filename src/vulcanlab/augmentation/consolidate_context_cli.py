"""
Command-line interface for context consolidation.

Usage:
    venv\\Scripts\\python -m vulcanlab.augmentation.consolidate_context_cli 1
    venv\\Scripts\\python -m vulcanlab.augmentation.consolidate_context_cli 1 -v
"""

import argparse
import sys

from .consolidate_context import (
    consolidate_context,
    DEFAULT_COVERAGE_THRESHOLD,
    DEFAULT_LINE_GAP
)


def main() -> int:
    """Main entry point for the command-line interface.

    Returns:
        Exit code (0 for success, 1 for error).
    """
    parser = argparse.ArgumentParser(
        description="Consolidate retrieved context by grouping and merging chunks.",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  %(prog)s 1                  # Consolidate for query ID 1
  %(prog)s 1 -v               # Verbose output
  %(prog)s 1 --coverage 0.6   # Use 60%% coverage threshold
        """
    )

    parser.add_argument(
        "query_id",
        type=int,
        help="ID of the query to consolidate"
    )

    parser.add_argument(
        "-v", "--verbose",
        action="store_true",
        help="Print progress information"
    )

    parser.add_argument(
        "--coverage",
        type=float,
        default=DEFAULT_COVERAGE_THRESHOLD,
        help=f"Coverage threshold for parent replacement (default: {DEFAULT_COVERAGE_THRESHOLD})"
    )

    parser.add_argument(
        "--line-gap",
        type=int,
        default=DEFAULT_LINE_GAP,
        help=f"Max line gap for merging adjacent chunks (default: {DEFAULT_LINE_GAP})"
    )

    args = parser.parse_args()

    try:
        result = consolidate_context(
            query_id=args.query_id,
            coverage_threshold=args.coverage,
            line_gap=args.line_gap,
            verbose=args.verbose
        )

        # Display results
        print("\n" + "=" * 70)
        print("CONSOLIDATION RESULTS")
        print("=" * 70)

        print(f"\nQuery ID: {result.query_id}")
        print(f"Original items: {result.original_count}")
        print(f"Consolidated groups: {result.consolidated_count}")

        print("\n" + "-" * 70)
        print("CONSOLIDATED GROUPS")
        print("-" * 70)

        for i, group in enumerate(result.groups, 1):
            # Truncate content for display
            content_preview = group.content[:350]
            if len(group.content) > 350:
                content_preview += "..."

            print(f"\n{i}. Chunk IDs: {group.chunk_ids}")
            print(f"   Work ID: {group.work_id} | Parent ID: {group.parent_id}")
            print(f"   Lines: {group.start_line}-{group.end_line} | Score: {group.score:.4f}")
            print(f"   Content: {content_preview}")

        print("\n" + "=" * 70)
        print(f"Results saved to query.clean_retrieval_context")
        print("=" * 70 + "\n")

        return 0

    except ValueError as e:
        print(f"Error: {e}", file=sys.stderr)
        return 1
    except RuntimeError as e:
        print(f"Error: {e}", file=sys.stderr)
        return 1
    except KeyboardInterrupt:
        print("\nCancelled by user.")
        return 1
    except Exception as e:
        print(f"Unexpected error: {e}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    sys.exit(main())
