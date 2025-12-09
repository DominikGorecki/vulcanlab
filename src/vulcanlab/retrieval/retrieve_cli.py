"""
Command-line interface for retrieval.

Usage:
    venv\\Scripts\\python -m vulcanlab.retrieval.retrieve_cli 1
    venv\\Scripts\\python -m vulcanlab.retrieval.retrieve_cli 1 -v
    venv\\Scripts\\python -m vulcanlab.retrieval.retrieve_cli 1 --top-n 20
"""

import argparse
import sys

from .retrieve import (
    retrieve,
    DEFAULT_DENSE_LIMIT,
    DEFAULT_LEXICAL_LIMIT,
    DEFAULT_RRF_K,
    DEFAULT_TOP_K_RRF,
    DEFAULT_TOP_N_FINAL,
    DEFAULT_ENTITY_BOOST
)


def main() -> int:
    """Main entry point for the command-line interface.

    Returns:
        Exit code (0 for success, 1 for error).
    """
    parser = argparse.ArgumentParser(
        description="Retrieve relevant chunks for a query using dense + lexical + RRF + BGE reranking.",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  %(prog)s 1                  # Retrieve for query ID 1
  %(prog)s 1 -v               # Verbose output
  %(prog)s 1 --top-n 20       # Return top 20 instead of 12
        """
    )

    parser.add_argument(
        "query_id",
        type=int,
        help="ID of the query to retrieve for"
    )

    parser.add_argument(
        "-v", "--verbose",
        action="store_true",
        help="Print progress information"
    )

    parser.add_argument(
        "--dense-limit",
        type=int,
        default=DEFAULT_DENSE_LIMIT,
        help=f"Max results per dense query (default: {DEFAULT_DENSE_LIMIT})"
    )

    parser.add_argument(
        "--lexical-limit",
        type=int,
        default=DEFAULT_LEXICAL_LIMIT,
        help=f"Max results per lexical query (default: {DEFAULT_LEXICAL_LIMIT})"
    )

    parser.add_argument(
        "--rrf-k",
        type=int,
        default=DEFAULT_RRF_K,
        help=f"RRF constant (default: {DEFAULT_RRF_K})"
    )

    parser.add_argument(
        "--top-k-rrf",
        type=int,
        default=DEFAULT_TOP_K_RRF,
        help=f"Top candidates after RRF (default: {DEFAULT_TOP_K_RRF})"
    )

    parser.add_argument(
        "--top-n",
        type=int,
        default=DEFAULT_TOP_N_FINAL,
        help=f"Final number of results (default: {DEFAULT_TOP_N_FINAL})"
    )

    parser.add_argument(
        "--entity-boost",
        type=float,
        default=DEFAULT_ENTITY_BOOST,
        help=f"Score boost per entity match (default: {DEFAULT_ENTITY_BOOST})"
    )

    args = parser.parse_args()

    try:
        result = retrieve(
            query_id=args.query_id,
            dense_limit=args.dense_limit,
            lexical_limit=args.lexical_limit,
            rrf_k=args.rrf_k,
            top_k_rrf=args.top_k_rrf,
            top_n_final=args.top_n,
            entity_boost=args.entity_boost,
            verbose=args.verbose
        )

        # Display results
        print("\n" + "=" * 70)
        print("RETRIEVAL RESULTS")
        print("=" * 70)

        print(f"\nQuery ID: {result.query_id}")
        print(f"Dense candidates: {result.total_dense_candidates}")
        print(f"Lexical candidates: {result.total_lexical_candidates}")
        print(f"RRF unique candidates: {result.rrf_candidates}")
        print(f"Final results: {result.final_count}")

        print("\n" + "-" * 70)
        print("TOP RETRIEVED CHUNKS")
        print("-" * 70)

        for i, chunk in enumerate(result.chunks, 1):
            # Truncate content for display
            content_preview = chunk.content[:350]
            if len(chunk.content) > 350:
                content_preview += "..."

            print(f"\n{i}. Chunk ID: {chunk.id}")
            print(f"   Work ID: {chunk.work_id} | Level: {chunk.level}")
            print(f"   Final Score: {chunk.final_score:.4f} (rerank: {chunk.rerank_score:.4f}, entity: +{chunk.entity_boost:.4f})")
            print(f"   Content: {content_preview}")

        print("\n" + "=" * 70)
        print(f"Results saved to query.retrieved_context")
        print("=" * 70 + "\n")

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
