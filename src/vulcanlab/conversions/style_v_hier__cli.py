"""
CLI for Style vs Hier Markdown Selector.

Command-line interface for comparing and selecting the better structured markdown file
between style-based and hierarchy-based PDF conversions.

Example:
    python -m vulcanlab.conversions.style_v_hier__cli test.style.md test.hier.md -v
    python -m vulcanlab.conversions.style_v_hier__cli test.style.md test.hier.md --dry-run
"""

import argparse
import sys
from pathlib import Path

from .style_v_hier import (
    ChunkSizeConfig,
    ScoringWeights,
    compare_and_select,
    rename_files,
)


def main() -> int:
    """
    Main entry point for the CLI.

    Returns:
        Exit code (0 for success, 1 for error).
    """
    parser = argparse.ArgumentParser(
        description="Compare and select the better structured markdown file.",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  %(prog)s test.style.md test.hier.md
  %(prog)s test.style.md test.hier.md -v
  %(prog)s test.style.md test.hier.md --dry-run
  %(prog)s output/doc.style.md output/doc.hier.md -v

This tool analyzes both files and selects the one with:
  - Better heading hierarchy (H1-H4 structure)
  - More chunk-friendly sections (150-400 words)
  - Even distribution of major sections
  - Fewer structural problems

The winner is copied to <file>.md
Both original files (.style.md and .hier.md) remain untouched
        """
    )

    parser.add_argument(
        "style_path",
        type=str,
        help="Path to style-based markdown file (e.g., test.style.md)"
    )

    parser.add_argument(
        "hier_path",
        type=str,
        help="Path to hierarchy-based markdown file (e.g., test.hier.md)"
    )

    parser.add_argument(
        "-v", "--verbose",
        action="store_true",
        help="Print detailed scoring breakdown"
    )

    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Show results without copying the winner to <file>.md"
    )

    # Optional configuration overrides
    parser.add_argument(
        "--target-min",
        type=int,
        default=150,
        help="Minimum words for target chunk size (default: 150)"
    )

    parser.add_argument(
        "--target-max",
        type=int,
        default=400,
        help="Maximum words for target chunk size (default: 400)"
    )

    parser.add_argument(
        "--small-threshold",
        type=int,
        default=50,
        help="Threshold for 'too small' sections in words (default: 50)"
    )

    parser.add_argument(
        "--large-threshold",
        type=int,
        default=800,
        help="Threshold for 'too large' sections in words (default: 800)"
    )

    parser.add_argument(
        "--weight-hierarchy",
        type=float,
        default=0.40,
        help="Weight for hierarchy score (default: 0.40)"
    )

    parser.add_argument(
        "--weight-chunkability",
        type=float,
        default=0.40,
        help="Weight for chunkability score (default: 0.40)"
    )

    parser.add_argument(
        "--weight-coverage",
        type=float,
        default=0.20,
        help="Weight for coverage score (default: 0.20)"
    )

    args = parser.parse_args()

    try:
        # Validate paths
        style_path = Path(args.style_path)
        hier_path = Path(args.hier_path)

        if not style_path.exists():
            print(f"Error: Style file not found: {style_path}", file=sys.stderr)
            return 1

        if not hier_path.exists():
            print(f"Error: Hier file not found: {hier_path}", file=sys.stderr)
            return 1

        # Configure scoring
        weights = ScoringWeights(
            hierarchy=args.weight_hierarchy,
            chunkability=args.weight_chunkability,
            coverage=args.weight_coverage
        )

        config = ChunkSizeConfig(
            target_min=args.target_min,
            target_max=args.target_max,
            small_threshold=args.small_threshold,
            large_threshold=args.large_threshold
        )

        # Validate weights sum to ~1.0
        weight_sum = weights.hierarchy + weights.chunkability + weights.coverage
        if abs(weight_sum - 1.0) > 0.01:
            print(f"Warning: Weights sum to {weight_sum:.2f}, not 1.0", file=sys.stderr)

        # Compare and select
        print(f"Comparing {style_path.name} vs {hier_path.name}...")

        winner = compare_and_select(
            style_path,
            hier_path,
            weights=weights,
            config=config,
            verbose=args.verbose
        )

        loser = hier_path if winner == style_path else style_path

        # Determine output filename
        stem = winner.stem
        if stem.endswith('.style'):
            base_stem = stem[:-6]
        elif stem.endswith('.hier'):
            base_stem = stem[:-5]
        else:
            base_stem = stem
        output_name = f"{base_stem}.md"

        # Copy winner unless dry-run
        if args.dry_run:
            print(f"\nDry run - would copy:")
            print(f"  Winner: {winner.name} -> {output_name}")
            print(f"  Original files remain untouched")
        else:
            rename_files(winner, loser, verbose=args.verbose or True)
            print(f"\nWinner copied successfully to {output_name}")

        return 0

    except FileNotFoundError as e:
        print(f"Error: {e}", file=sys.stderr)
        return 1
    except Exception as e:
        print(f"Error: {e}", file=sys.stderr)
        if args.verbose:
            import traceback
            traceback.print_exc()
        return 1


if __name__ == "__main__":
    sys.exit(main())
