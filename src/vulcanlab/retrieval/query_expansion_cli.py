"""
Command-line interface for query expansion.

Usage:
    venv\\Scripts\\python -m vulcanlab.retrieval.query_expansion_cli "What is working memory?"
    venv\\Scripts\\python -m vulcanlab.retrieval.query_expansion_cli "Compare CBT and DBT" -n 5 -v
"""

import argparse
import sys

from .query_expansion import expand_query


def main() -> int:
    """Main entry point for the command-line interface.

    Returns:
        Exit code (0 for success, 1 for error).
    """
    parser = argparse.ArgumentParser(
        description="Expand a query using MQE and HyDE for RAG retrieval.",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  %(prog)s "What is working memory?"
  %(prog)s "Compare CBT vs DBT" -n 5
  %(prog)s "How does neuroplasticity work?" -v
        """
    )

    parser.add_argument(
        "query",
        help="The query to expand"
    )

    parser.add_argument(
        "-n", "--num-queries",
        type=int,
        default=3,
        help="Number of alternative queries to generate (default: 3)"
    )

    parser.add_argument(
        "-v", "--verbose",
        action="store_true",
        help="Print progress information"
    )

    args = parser.parse_args()

    try:
        result = expand_query(
            query=args.query,
            n=args.num_queries,
            verbose=args.verbose
        )

        # Display results in human-readable format
        print("\n" + "=" * 60)
        print("QUERY EXPANSION RESULTS")
        print("=" * 60)

        print(f"\nOriginal Query: {result.original_query}")

        print(f"\nIntent: {result.intent}")

        print("\nExpanded Queries:")
        for i, q in enumerate(result.expanded_queries, 1):
            print(f"  {i}. {q}")

        print("\nHyDE Answer:")
        print(f"  {result.hyde_answer}")

        print("\nEntities:")
        if result.entities:
            for entity in result.entities:
                print(f"  - {entity}")
        else:
            print("  (none detected)")

        print(f"\nSaved to database with ID: {result.query_id}")
        print("Vector status: to_vec (embeddings pending)")
        print("=" * 60 + "\n")

        return 0

    except ValueError as e:
        print(f"Error: {e}", file=sys.stderr)
        return 1
    except Exception as e:
        print(f"Unexpected error: {e}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    sys.exit(main())
