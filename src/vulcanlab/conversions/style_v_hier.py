"""
Style vs Hier Markdown Selector.

This module analyzes two markdown files (style-based and hierarchy-based conversions)
and selects the better structured one based on structural metrics, chunkability,
and various heuristics optimized for RAG chunking.

Example:
    from vulcanlab.conversions.style_v_hier import compare_and_select

    winner = compare_and_select(
        Path("output/test.style.md"),
        Path("output/test.hier.md"),
        verbose=True
    )
"""

import re
import shutil
import statistics
from dataclasses import dataclass, field
from pathlib import Path
from typing import Optional


@dataclass
class ChunkSizeConfig:
    """Configuration for chunk size thresholds."""

    target_min: int = 150  # Minimum words for target range
    target_max: int = 400  # Maximum words for target range
    small_threshold: int = 50  # Threshold for "too small" sections
    large_threshold: int = 800  # Threshold for "too large" sections
    words_per_line: float = 12.0  # Estimated words per line for markdown


@dataclass
class ScoringWeights:
    """Weights for different scoring components."""

    hierarchy: float = 0.40  # Weight for hierarchical correctness
    chunkability: float = 0.40  # Weight for chunk-friendly structure
    coverage: float = 0.20  # Weight for heading coverage/evenness


@dataclass
class Heading:
    """Represents a markdown heading with its metadata."""

    level: int  # 1-6 for H1-H6
    text: str  # Heading text (normalized)
    line_number: int  # Line where heading appears
    section_start: int = 0  # Start line of section content
    section_end: int = 0  # End line of section (exclusive)
    section_lines: int = 0  # Number of lines in section
    section_words: int = 0  # Estimated words in section


@dataclass
class StructuralMetrics:
    """Computed metrics for a markdown document."""

    total_headings: int = 0
    h1_h2_count: int = 0
    max_depth: int = 0
    avg_depth: float = 0.0

    # Coverage metrics
    coverage_score: float = 0.0
    h1_h2_spacing_variance: float = 0.0

    # Hierarchy metrics
    hierarchy_score: float = 0.0
    level_jump_count: int = 0
    avg_level_jump: float = 0.0

    # Chunkability metrics
    chunkability_score: float = 0.0
    target_size_sections: int = 0
    small_sections: int = 0
    large_sections: int = 0

    # Penalties
    penalty_total: float = 0.0
    repeated_heading_penalty: float = 0.0
    heading_run_penalty: float = 0.0
    imbalance_penalty: float = 0.0

    # Final score
    final_score: float = 0.0


def extract_headings(md_path: Path) -> list[Heading]:
    """
    Extract all ATX-style headings from a markdown file.

    Args:
        md_path: Path to markdown file.

    Returns:
        List of Heading objects with line numbers and text.
    """
    headings = []
    heading_pattern = re.compile(r'^(#{1,6})\s+(.+)$')

    with open(md_path, 'r', encoding='utf-8') as f:
        lines = f.readlines()

    for i, line in enumerate(lines, start=1):
        match = heading_pattern.match(line.strip())
        if match:
            level = len(match.group(1))
            text = match.group(2).strip()
            headings.append(Heading(
                level=level,
                text=text,
                line_number=i,
                section_start=i
            ))

    return headings


def compute_section_sizes(headings: list[Heading], total_lines: int, config: ChunkSizeConfig) -> None:
    """
    Compute section boundaries and sizes for all headings.

    Modifies headings in-place to set section_end, section_lines, and section_words.

    Args:
        headings: List of Heading objects.
        total_lines: Total number of lines in the document.
        config: Chunk size configuration for word estimation.
    """
    for i, heading in enumerate(headings):
        # Find the next heading at the same or higher level (lower number)
        section_end = total_lines + 1
        for j in range(i + 1, len(headings)):
            if headings[j].level <= heading.level:
                section_end = headings[j].line_number
                break

        heading.section_end = section_end
        heading.section_lines = section_end - heading.section_start
        heading.section_words = int(heading.section_lines * config.words_per_line)


def compute_coverage_score(headings: list[Heading], total_lines: int) -> float:
    """
    Compute coverage score based on H1/H2 distribution and evenness.

    Args:
        headings: List of Heading objects.
        total_lines: Total number of lines in the document.

    Returns:
        Coverage score (0.0-1.0).
    """
    h1_h2_headings = [h for h in headings if h.level in (1, 2)]

    if len(h1_h2_headings) == 0:
        return 0.0

    # Score for number of H1/H2 headings (more is better, up to a limit)
    count_score = min(len(h1_h2_headings) / 10.0, 1.0)  # Cap at 10 major sections

    # Score for spacing evenness
    if len(h1_h2_headings) >= 2:
        spacings = []
        for i in range(len(h1_h2_headings) - 1):
            spacing = h1_h2_headings[i + 1].line_number - h1_h2_headings[i].line_number
            spacings.append(spacing)

        # Lower variance = more even spacing = higher score
        variance = statistics.variance(spacings) if len(spacings) > 1 else 0
        # Normalize variance by document length
        normalized_variance = variance / (total_lines ** 2) if total_lines > 0 else 0
        evenness_score = max(0.0, 1.0 - (normalized_variance * 100))
    else:
        evenness_score = 0.5  # Single H1/H2 gets middle score

    # Combine scores
    return (count_score * 0.6) + (evenness_score * 0.4)


def compute_hierarchy_score(headings: list[Heading]) -> tuple[float, int, float]:
    """
    Compute hierarchy score based on depth usage and level transitions.

    Args:
        headings: List of Heading objects.

    Returns:
        Tuple of (hierarchy_score, level_jump_count, avg_level_jump).
    """
    if len(headings) == 0:
        return 0.0, 0, 0.0

    # Compute depth metrics
    max_depth = max(h.level for h in headings)
    avg_depth = statistics.mean(h.level for h in headings)

    # Ideal: max depth of 3-4, average depth around 2-3
    depth_score = 1.0
    if max_depth == 1:
        depth_score = 0.3  # Only H1 - bad
    elif max_depth == 2:
        depth_score = 0.7  # H1-H2 only - okay
    elif max_depth <= 4:
        depth_score = 1.0  # H1-H4 - good
    else:
        depth_score = 0.9  # H5-H6 used - slightly penalize

    # Analyze level transitions
    level_jumps = []
    for i in range(len(headings) - 1):
        jump = headings[i + 1].level - headings[i].level
        level_jumps.append(abs(jump))

    if len(level_jumps) == 0:
        return depth_score, 0, 0.0

    # Count big jumps (>2 levels)
    big_jumps = sum(1 for j in level_jumps if j > 2)
    avg_jump = statistics.mean(level_jumps)

    # Penalize big jumps
    transition_score = max(0.0, 1.0 - (big_jumps / len(level_jumps) * 2.0))

    # Combine scores
    hierarchy_score = (depth_score * 0.5) + (transition_score * 0.5)

    return hierarchy_score, big_jumps, avg_jump


def compute_chunkability_score(headings: list[Heading], config: ChunkSizeConfig) -> tuple[float, int, int, int]:
    """
    Compute chunkability score based on section sizes.

    Args:
        headings: List of Heading objects.
        config: Chunk size configuration.

    Returns:
        Tuple of (chunkability_score, target_count, small_count, large_count).
    """
    if len(headings) == 0:
        return 0.0, 0, 0, 0

    target_count = 0
    small_count = 0
    large_count = 0

    for heading in headings:
        words = heading.section_words
        if config.target_min <= words <= config.target_max:
            target_count += 1
        elif words < config.small_threshold:
            small_count += 1
        elif words > config.large_threshold:
            large_count += 1

    total_sections = len(headings)

    # Score calculation
    target_score = target_count / total_sections
    small_penalty = (small_count / total_sections) * 0.3
    large_penalty = (large_count / total_sections) * 0.5

    chunkability_score = max(0.0, target_score - small_penalty - large_penalty)

    return chunkability_score, target_count, small_count, large_count


def compute_penalties(headings: list[Heading], total_lines: int) -> tuple[float, float, float, float]:
    """
    Compute penalties for structural problems.

    Args:
        headings: List of Heading objects.
        total_lines: Total number of lines in the document.

    Returns:
        Tuple of (total_penalty, repeated_penalty, heading_run_penalty, imbalance_penalty).
    """
    repeated_penalty = 0.0
    heading_run_penalty = 0.0
    imbalance_penalty = 0.0

    if len(headings) == 0:
        return 0.0, 0.0, 0.0, 0.0

    # 1. Repeated junk headings penalty
    heading_counts = {}
    for h in headings:
        normalized = h.text.lower().strip()
        heading_counts[normalized] = heading_counts.get(normalized, 0) + 1

    for text, count in heading_counts.items():
        if count >= 3:
            # Check if these repeated headings have minimal content
            repeated_headings = [h for h in headings if h.text.lower().strip() == text]
            avg_content = statistics.mean(h.section_words for h in repeated_headings)
            if avg_content < 30:  # Less than 30 words on average
                repeated_penalty += 5.0

    # 2. Heading-only runs penalty
    consecutive_short = 0
    for i in range(len(headings) - 1):
        gap = headings[i + 1].line_number - headings[i].line_number
        if gap <= 2:  # Heading followed immediately by another heading
            consecutive_short += 1
            if consecutive_short >= 5:
                heading_run_penalty = 10.0
                break
        else:
            consecutive_short = 0

    # 3. Extreme imbalance penalty
    if len(headings) > 1:
        total_words = sum(h.section_words for h in headings)
        if total_words > 0:
            largest_section = max(h.section_words for h in headings)
            if largest_section / total_words > 0.5:  # One section is >50% of document
                imbalance_penalty = 15.0

    total_penalty = repeated_penalty + heading_run_penalty + imbalance_penalty

    return total_penalty, repeated_penalty, heading_run_penalty, imbalance_penalty


def compute_final_score(
    headings: list[Heading],
    total_lines: int,
    weights: ScoringWeights,
    config: ChunkSizeConfig
) -> StructuralMetrics:
    """
    Compute all metrics and final score for a markdown document.

    Args:
        headings: List of Heading objects.
        total_lines: Total number of lines in the document.
        weights: Scoring weights configuration.
        config: Chunk size configuration.

    Returns:
        StructuralMetrics object with all computed scores.
    """
    metrics = StructuralMetrics()

    if len(headings) == 0:
        return metrics

    # Basic counts
    metrics.total_headings = len(headings)
    metrics.h1_h2_count = sum(1 for h in headings if h.level in (1, 2))
    metrics.max_depth = max(h.level for h in headings)
    metrics.avg_depth = statistics.mean(h.level for h in headings)

    # Compute section sizes
    compute_section_sizes(headings, total_lines, config)

    # Coverage score
    metrics.coverage_score = compute_coverage_score(headings, total_lines)

    # Hierarchy score
    hierarchy_score, jump_count, avg_jump = compute_hierarchy_score(headings)
    metrics.hierarchy_score = hierarchy_score
    metrics.level_jump_count = jump_count
    metrics.avg_level_jump = avg_jump

    # Chunkability score
    chunk_score, target, small, large = compute_chunkability_score(headings, config)
    metrics.chunkability_score = chunk_score
    metrics.target_size_sections = target
    metrics.small_sections = small
    metrics.large_sections = large

    # Penalties
    total_pen, rep_pen, run_pen, imb_pen = compute_penalties(headings, total_lines)
    metrics.penalty_total = total_pen
    metrics.repeated_heading_penalty = rep_pen
    metrics.heading_run_penalty = run_pen
    metrics.imbalance_penalty = imb_pen

    # Final weighted score
    weighted_score = (
        metrics.hierarchy_score * weights.hierarchy +
        metrics.chunkability_score * weights.chunkability +
        metrics.coverage_score * weights.coverage
    )

    # Apply penalties (normalize to 0-1 range, max penalty ~30)
    penalty_factor = min(metrics.penalty_total / 30.0, 1.0)
    metrics.final_score = max(0.0, weighted_score - penalty_factor)

    return metrics


def compare_and_select(
    style_path: Path,
    hier_path: Path,
    weights: Optional[ScoringWeights] = None,
    config: Optional[ChunkSizeConfig] = None,
    verbose: bool = False
) -> Path:
    """
    Compare two markdown files and select the better structured one.

    Args:
        style_path: Path to style-based markdown file.
        hier_path: Path to hierarchy-based markdown file.
        weights: Optional scoring weights (uses defaults if None).
        config: Optional chunk size config (uses defaults if None).
        verbose: If True, print detailed scoring information.

    Returns:
        Path to the winning markdown file.

    Raises:
        FileNotFoundError: If either file doesn't exist.
    """
    if not style_path.exists():
        raise FileNotFoundError(f"Style file not found: {style_path}")
    if not hier_path.exists():
        raise FileNotFoundError(f"Hier file not found: {hier_path}")

    weights = weights or ScoringWeights()
    config = config or ChunkSizeConfig()

    # Process style file
    style_headings = extract_headings(style_path)
    style_lines = len(style_path.read_text(encoding='utf-8').splitlines())
    style_metrics = compute_final_score(style_headings, style_lines, weights, config)

    # Process hier file
    hier_headings = extract_headings(hier_path)
    hier_lines = len(hier_path.read_text(encoding='utf-8').splitlines())
    hier_metrics = compute_final_score(hier_headings, hier_lines, weights, config)

    if verbose:
        print(f"\n=== Style-based Analysis ({style_path.name}) ===")
        print(f"Total headings: {style_metrics.total_headings}")
        print(f"H1/H2 count: {style_metrics.h1_h2_count}")
        print(f"Max depth: {style_metrics.max_depth}, Avg depth: {style_metrics.avg_depth:.2f}")
        print(f"Coverage score: {style_metrics.coverage_score:.3f}")
        print(f"Hierarchy score: {style_metrics.hierarchy_score:.3f} (jumps: {style_metrics.level_jump_count})")
        print(f"Chunkability score: {style_metrics.chunkability_score:.3f}")
        print(f"  Target size: {style_metrics.target_size_sections}, Small: {style_metrics.small_sections}, Large: {style_metrics.large_sections}")
        print(f"Penalties: {style_metrics.penalty_total:.1f}")
        print(f"FINAL SCORE: {style_metrics.final_score:.4f}")

        print(f"\n=== Hierarchy-based Analysis ({hier_path.name}) ===")
        print(f"Total headings: {hier_metrics.total_headings}")
        print(f"H1/H2 count: {hier_metrics.h1_h2_count}")
        print(f"Max depth: {hier_metrics.max_depth}, Avg depth: {hier_metrics.avg_depth:.2f}")
        print(f"Coverage score: {hier_metrics.coverage_score:.3f}")
        print(f"Hierarchy score: {hier_metrics.hierarchy_score:.3f} (jumps: {hier_metrics.level_jump_count})")
        print(f"Chunkability score: {hier_metrics.chunkability_score:.3f}")
        print(f"  Target size: {hier_metrics.target_size_sections}, Small: {hier_metrics.small_sections}, Large: {hier_metrics.large_sections}")
        print(f"Penalties: {hier_metrics.penalty_total:.1f}")
        print(f"FINAL SCORE: {hier_metrics.final_score:.4f}")

    # Determine winner
    score_diff = abs(style_metrics.final_score - hier_metrics.final_score)

    if score_diff < 0.01:  # Scores are tied
        # Tie-breaker 1: Better chunkability
        if style_metrics.chunkability_score != hier_metrics.chunkability_score:
            winner = style_path if style_metrics.chunkability_score > hier_metrics.chunkability_score else hier_path
        # Tie-breaker 2: Fewer level jumps
        elif style_metrics.level_jump_count != hier_metrics.level_jump_count:
            winner = style_path if style_metrics.level_jump_count < hier_metrics.level_jump_count else hier_path
        # Tie-breaker 3: More H1/H2 structure
        elif style_metrics.h1_h2_count != hier_metrics.h1_h2_count:
            winner = style_path if style_metrics.h1_h2_count > hier_metrics.h1_h2_count else hier_path
        # Tie-breaker 4: Deterministic - prefer hier
        else:
            winner = hier_path
    else:
        winner = style_path if style_metrics.final_score > hier_metrics.final_score else hier_path

    if verbose:
        print(f"\n=== Winner: {winner.name} ===")
        if score_diff < 0.01:
            print("(Decided by tie-breaking rules)")

    return winner


def rename_files(winner: Path, loser: Path, verbose: bool = False) -> None:
    """
    Copy winning file to <file>.md.

    The winner is copied (not renamed) to <file>.md.
    Both .style.md and .hier.md files remain untouched.

    Args:
        winner: Path to the winning markdown file.
        loser: Path to the losing markdown file (unused but kept for compatibility).
        verbose: If True, print copy actions.

    Raises:
        FileExistsError: If <file>.md already exists.
    """
    # Determine base name from winner
    # winner is either <file>.style.md or <file>.hier.md
    stem = winner.stem
    if stem.endswith('.style'):
        base_stem = stem[:-6]  # Remove '.style'
    elif stem.endswith('.hier'):
        base_stem = stem[:-5]  # Remove '.hier'
    else:
        base_stem = stem

    # Target path
    final_path = winner.parent / f"{base_stem}.md"

    # Check if target already exists
    if final_path.exists():
        raise FileExistsError(
            f"Output file already exists: {final_path}\n"
            f"Remove the existing file before running comparison."
        )

    # Copy winner to final path
    shutil.copy2(winner, final_path)
    if verbose:
        print(f"Copied winner: {winner.name} -> {final_path.name}")
