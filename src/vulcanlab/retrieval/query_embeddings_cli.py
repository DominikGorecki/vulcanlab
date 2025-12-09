"""
Command-line interface for query embeddings vectorization.

Usage:
    venv\\Scripts\\python -m vulcanlab.retrieval.query_embeddings_cli 1
    venv\\Scripts\\python -m vulcanlab.retrieval.query_embeddings_cli --all
    venv\\Scripts\\python -m vulcanlab.retrieval.query_embeddings_cli --all -v
"""

import argparse
import sys

from .query_embeddings import (
    vectorize_query,
    vectorize_all_queries,
    get_pending_queries_count
)


def main() -> int:
    """Main entry point for the command-line interface.

    Returns:
        Exit code (0 for success, 1 for error).
    """
    parser = argparse.ArgumentParser(
        description="Vectorize query embeddings for RAG retrieval.",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  %(prog)s 1                  # Vectorize query with ID 1
  %(prog)s --all              # Vectorize all pending queries
  %(prog)s --all -v           # Verbose output for all pending
        """
    )

    parser.add_argument(
        "query_id",
        type=int,
        nargs="?",
        help="ID of the query to vectorize"
    )

    parser.add_argument(
        "--all",
        action="store_true",
        help="Vectorize all queries with vector_status='to_vec'"
    )

    parser.add_argument(
        "-v", "--verbose",
        action="store_true",
        help="Print progress information"
    )

    args = parser.parse_args()

    # Validate arguments
    if not args.query_id and not args.all:
        parser.error("Either query_id or --all must be specified")

    if args.query_id and args.all:
        parser.error("Cannot specify both query_id and --all")

    try:
        if args.all:
            # Process all pending queries
            pending_count = get_pending_queries_count()

            if pending_count == 0:
                print("No queries pending vectorization (vector_status='to_vec')")
                return 0

            # Estimate total embeddings (rough estimate: ~5 per query)
            estimated_embeddings = pending_count * 5

            if estimated_embeddings > 500:
                print(f"Warning: About to generate ~{estimated_embeddings} embeddings for {pending_count} queries.")
                response = input("Continue? (Y/n): ").strip().lower()
                if response and response != 'y':
                    print("Cancelled.")
                    return 0

            result = vectorize_all_queries(verbose=args.verbose)

            # Display results
            print("\n" + "=" * 60)
            print("BATCH VECTORIZATION RESULTS")
            print("=" * 60)
            print(f"\nTotal queries processed: {result.processed}")
            print(f"Successful: {result.success}")
            print(f"Failed: {result.failed}")
            print(f"Total embeddings generated: {result.total_embeddings}")

            if result.errors:
                print("\nErrors:")
                for query_id, error in result.errors:
                    print(f"  Query {query_id}: {error}")

            print("=" * 60 + "\n")

        else:
            # Process single query
            result = vectorize_query(
                query_id=args.query_id,
                verbose=args.verbose
            )

            # Display results
            print("\n" + "=" * 60)
            print("QUERY VECTORIZATION RESULTS")
            print("=" * 60)
            print(f"\nQuery ID: {result.query_id}")

            if result.success:
                print(f"Status: Success")
                print(f"Generated {result.total_embeddings} embeddings:")
                print(f"  - {result.original_count} original")
                print(f"  - {result.mqe_count} MQE")
                print(f"  - {result.hyde_count} HyDE")
                print(f"Vector status: vec")
            else:
                print(f"Status: Failed")
                print(f"Error: {result.error}")
                print(f"Vector status: vec_err")

            print("=" * 60 + "\n")

            if not result.success:
                return 1

        return 0

    except ValueError as e:
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
