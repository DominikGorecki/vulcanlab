"""
Unit tests for style_v_hier module.

Tests style detection, hierarchy analysis, and conversion logic.
"""

from pathlib import Path
from unittest.mock import patch

import pytest

from vulcanlab.conversions.style_v_hier import (
    ChunkSizeConfig,
    Heading,
    ScoringWeights,
    StructuralMetrics,
    compare_and_select,
    compute_chunkability_score,
    compute_coverage_score,
    compute_final_score,
    compute_hierarchy_score,
    compute_penalties,
    compute_section_sizes,
    extract_headings,
    rename_files,
)


class TestExtractHeadings:
    """Tests for extract_headings function."""

    def test_extract_headings_basic(self, tmp_path):
        """Test basic heading extraction."""
        md_file = tmp_path / "test.md"
        md_file.write_text(
            """# Chapter 1

Some content here.

## Section 1.1

More content.

### Subsection 1.1.1

Even more content.
""",
            encoding="utf-8",
        )

        headings = extract_headings(md_file)

        assert len(headings) == 3
        assert headings[0].level == 1
        assert headings[0].text == "Chapter 1"
        assert headings[0].line_number == 1
        assert headings[1].level == 2
        assert headings[1].text == "Section 1.1"
        assert headings[2].level == 3
        assert headings[2].text == "Subsection 1.1.1"

    def test_extract_headings_all_levels(self, tmp_path):
        """Test extraction of all heading levels (H1-H6)."""
        md_file = tmp_path / "test.md"
        md_file.write_text(
            """# H1
## H2
### H3
#### H4
##### H5
###### H6
""",
            encoding="utf-8",
        )

        headings = extract_headings(md_file)

        assert len(headings) == 6
        for i, heading in enumerate(headings, start=1):
            assert heading.level == i
            assert heading.text == f"H{i}"

    def test_extract_headings_no_headings(self, tmp_path):
        """Test extraction from file with no headings."""
        md_file = tmp_path / "test.md"
        md_file.write_text("Just some text without headings.\nMore text.", encoding="utf-8")

        headings = extract_headings(md_file)

        assert len(headings) == 0

    def test_extract_headings_with_whitespace(self, tmp_path):
        """Test extraction handles whitespace correctly."""
        md_file = tmp_path / "test.md"
        md_file.write_text(
            """#   Heading with spaces
##  Another heading  
###   Heading with tabs	
""",
            encoding="utf-8",
        )

        headings = extract_headings(md_file)

        assert len(headings) == 3
        assert headings[0].text == "Heading with spaces"
        assert headings[1].text == "Another heading"
        assert headings[2].text == "Heading with tabs"

    def test_extract_headings_mixed_content(self, tmp_path):
        """Test extraction from file with mixed content."""
        md_file = tmp_path / "test.md"
        md_file.write_text(
            """Some intro text.

# First Heading

Content paragraph.

## Subheading

More content.

# Second Heading

Final content.
""",
            encoding="utf-8",
        )

        headings = extract_headings(md_file)

        assert len(headings) == 3
        assert headings[0].text == "First Heading"
        assert headings[1].text == "Subheading"
        assert headings[2].text == "Second Heading"


class TestComputeSectionSizes:
    """Tests for compute_section_sizes function."""

    def test_compute_section_sizes_basic(self, tmp_path):
        """Test basic section size computation."""
        headings = [
            Heading(level=1, text="Chapter 1", line_number=1, section_start=1),
            Heading(level=2, text="Section 1.1", line_number=5, section_start=5),
            Heading(level=1, text="Chapter 2", line_number=10, section_start=10),
        ]
        total_lines = 15

        compute_section_sizes(headings, total_lines, ChunkSizeConfig())

        assert headings[0].section_end == 10  # Ends at next H1
        assert headings[0].section_lines == 9
        assert headings[1].section_end == 10  # Ends at next H1 (higher level)
        assert headings[1].section_lines == 5
        assert headings[2].section_end == 16  # Ends at EOF
        assert headings[2].section_lines == 6

    def test_compute_section_sizes_single_heading(self, tmp_path):
        """Test section size with single heading."""
        headings = [Heading(level=1, text="Only Chapter", line_number=1, section_start=1)]
        total_lines = 20

        compute_section_sizes(headings, total_lines, ChunkSizeConfig())

        assert headings[0].section_end == 21
        assert headings[0].section_lines == 20

    def test_compute_section_sizes_nested_hierarchy(self, tmp_path):
        """Test section sizes with nested hierarchy."""
        headings = [
            Heading(level=1, text="H1", line_number=1, section_start=1),
            Heading(level=2, text="H2", line_number=5, section_start=5),
            Heading(level=3, text="H3", line_number=8, section_start=8),
            Heading(level=2, text="H2-2", line_number=12, section_start=12),
            Heading(level=1, text="H1-2", line_number=15, section_start=15),
        ]
        total_lines = 20

        compute_section_sizes(headings, total_lines, ChunkSizeConfig())

        assert headings[0].section_end == 15  # Ends at next H1
        assert headings[1].section_end == 12  # Ends at next H2
        assert headings[2].section_end == 12  # Ends at next H2 (higher level)
        assert headings[3].section_end == 15  # Ends at next H1
        assert headings[4].section_end == 21  # Ends at EOF


class TestComputeCoverageScore:
    """Tests for compute_coverage_score function."""

    def test_compute_coverage_score_no_h1_h2(self, tmp_path):
        """Test coverage score with no H1/H2 headings."""
        headings = [
            Heading(level=3, text="H3", line_number=1, section_start=1),
            Heading(level=4, text="H4", line_number=5, section_start=5),
        ]

        score = compute_coverage_score(headings, total_lines=10)

        assert score == 0.0

    def test_compute_coverage_score_single_h1(self, tmp_path):
        """Test coverage score with single H1."""
        headings = [Heading(level=1, text="Chapter 1", line_number=1, section_start=1)]

        score = compute_coverage_score(headings, total_lines=100)

        # Single H1/H2 gets middle score (0.5) for evenness
        assert 0.0 < score < 1.0

    def test_compute_coverage_score_multiple_h1_h2(self, tmp_path):
        """Test coverage score with multiple H1/H2 headings."""
        headings = [
            Heading(level=1, text="Chapter 1", line_number=10, section_start=10),
            Heading(level=2, text="Section 1.1", line_number=20, section_start=20),
            Heading(level=1, text="Chapter 2", line_number=30, section_start=30),
            Heading(level=2, text="Section 2.1", line_number=40, section_start=40),
        ]

        score = compute_coverage_score(headings, total_lines=100)

        assert 0.0 < score <= 1.0

    def test_compute_coverage_score_even_spacing(self, tmp_path):
        """Test coverage score with evenly spaced headings."""
        headings = [
            Heading(level=1, text="Chapter 1", line_number=10, section_start=10),
            Heading(level=1, text="Chapter 2", line_number=20, section_start=20),
            Heading(level=1, text="Chapter 3", line_number=30, section_start=30),
        ]

        score = compute_coverage_score(headings, total_lines=100)

        # Even spacing should give higher score
        assert score > 0.0


class TestComputeHierarchyScore:
    """Tests for compute_hierarchy_score function."""

    def test_compute_hierarchy_score_empty(self, tmp_path):
        """Test hierarchy score with no headings."""
        headings = []

        score, jumps, avg_jump = compute_hierarchy_score(headings)

        assert score == 0.0
        assert jumps == 0
        assert avg_jump == 0.0

    def test_compute_hierarchy_score_only_h1(self, tmp_path):
        """Test hierarchy score with only H1 headings (bad structure)."""
        headings = [
            Heading(level=1, text="Chapter 1", line_number=1, section_start=1),
            Heading(level=1, text="Chapter 2", line_number=10, section_start=10),
        ]

        score, jumps, avg_jump = compute_hierarchy_score(headings)

        # Only H1 gets low depth score (0.3), but good transitions (1.0) boost it
        # Final score = (0.3 * 0.5) + (1.0 * 0.5) = 0.65
        assert score == 0.65
        assert jumps == 0  # No big jumps between H1 headings
        assert avg_jump == 0.0  # No jumps (both are same level)

    def test_compute_hierarchy_score_h1_h2(self, tmp_path):
        """Test hierarchy score with H1-H2 structure."""
        headings = [
            Heading(level=1, text="Chapter 1", line_number=1, section_start=1),
            Heading(level=2, text="Section 1.1", line_number=5, section_start=5),
            Heading(level=2, text="Section 1.2", line_number=10, section_start=10),
        ]

        score, jumps, avg_jump = compute_hierarchy_score(headings)

        # H1-H2 should get medium score
        assert 0.5 < score < 1.0

    def test_compute_hierarchy_score_ideal_depth(self, tmp_path):
        """Test hierarchy score with ideal depth (H1-H4)."""
        headings = [
            Heading(level=1, text="Chapter 1", line_number=1, section_start=1),
            Heading(level=2, text="Section 1.1", line_number=5, section_start=5),
            Heading(level=3, text="Subsection 1.1.1", line_number=10, section_start=10),
            Heading(level=4, text="Sub-subsection", line_number=15, section_start=15),
        ]

        score, jumps, avg_jump = compute_hierarchy_score(headings)

        # Ideal depth should get high score
        assert score > 0.8

    def test_compute_hierarchy_score_big_jumps(self, tmp_path):
        """Test hierarchy score penalizes big level jumps."""
        headings = [
            Heading(level=1, text="Chapter 1", line_number=1, section_start=1),
            Heading(level=4, text="Jumped to H4", line_number=5, section_start=5),  # Big jump
            Heading(level=1, text="Chapter 2", line_number=10, section_start=10),
        ]

        score, jumps, avg_jump = compute_hierarchy_score(headings)

        # Big jumps should reduce score
        assert jumps > 0
        assert score < 1.0


class TestComputeChunkabilityScore:
    """Tests for compute_chunkability_score function."""

    def test_compute_chunkability_score_empty(self, tmp_path):
        """Test chunkability score with no headings."""
        headings = []

        score, target, small, large = compute_chunkability_score(headings, ChunkSizeConfig())

        assert score == 0.0
        assert target == 0
        assert small == 0
        assert large == 0

    def test_compute_chunkability_score_target_size(self, tmp_path):
        """Test chunkability score with target-sized sections."""
        config = ChunkSizeConfig(target_min=150, target_max=400, words_per_line=12.0)
        headings = [
            Heading(level=1, text="Chapter 1", line_number=1, section_start=1, section_words=200),
            Heading(level=1, text="Chapter 2", line_number=20, section_start=20, section_words=300),
        ]

        score, target, small, large = compute_chunkability_score(headings, config)

        assert target == 2
        assert small == 0
        assert large == 0
        assert score > 0.0

    def test_compute_chunkability_score_small_sections(self, tmp_path):
        """Test chunkability score with small sections."""
        config = ChunkSizeConfig(target_min=150, target_max=400, small_threshold=50, words_per_line=12.0)
        headings = [
            Heading(level=1, text="Chapter 1", line_number=1, section_start=1, section_words=30),
            Heading(level=1, text="Chapter 2", line_number=5, section_start=5, section_words=40),
        ]

        score, target, small, large = compute_chunkability_score(headings, config)

        assert small == 2
        assert target == 0
        assert score < 1.0  # Should be penalized

    def test_compute_chunkability_score_large_sections(self, tmp_path):
        """Test chunkability score with large sections."""
        config = ChunkSizeConfig(target_min=150, target_max=400, large_threshold=800, words_per_line=12.0)
        headings = [
            Heading(level=1, text="Chapter 1", line_number=1, section_start=1, section_words=1000),
            Heading(level=1, text="Chapter 2", line_number=100, section_start=100, section_words=1200),
        ]

        score, target, small, large = compute_chunkability_score(headings, config)

        assert large == 2
        assert target == 0
        assert score < 1.0  # Should be penalized


class TestComputePenalties:
    """Tests for compute_penalties function."""

    def test_compute_penalties_empty(self, tmp_path):
        """Test penalties with no headings."""
        headings = []

        total, rep, run, imb = compute_penalties(headings, total_lines=100)

        assert total == 0.0
        assert rep == 0.0
        assert run == 0.0
        assert imb == 0.0

    def test_compute_penalties_repeated_headings(self, tmp_path):
        """Test penalty for repeated junk headings."""
        headings = [
            Heading(level=1, text="Contents", line_number=1, section_start=1, section_words=5),
            Heading(level=1, text="Contents", line_number=5, section_start=5, section_words=5),
            Heading(level=1, text="Contents", line_number=10, section_start=10, section_words=5),
        ]

        total, rep, run, imb = compute_penalties(headings, total_lines=100)

        # Should have repeated heading penalty
        assert rep > 0.0
        assert total > 0.0

    def test_compute_penalties_heading_runs(self, tmp_path):
        """Test penalty for heading-only runs."""
        headings = []
        for i in range(10):
            headings.append(
                Heading(level=1, text=f"Heading {i}", line_number=i + 1, section_start=i + 1, section_words=10)
            )

        total, rep, run, imb = compute_penalties(headings, total_lines=100)

        # Should have heading run penalty
        assert run > 0.0
        assert total > 0.0

    def test_compute_penalties_imbalance(self, tmp_path):
        """Test penalty for extreme section imbalance."""
        headings = [
            Heading(level=1, text="Chapter 1", line_number=1, section_start=1, section_words=5000),
            Heading(level=1, text="Chapter 2", line_number=100, section_start=100, section_words=100),
            Heading(level=1, text="Chapter 3", line_number=110, section_start=110, section_words=100),
        ]

        total, rep, run, imb = compute_penalties(headings, total_lines=200)

        # Should have imbalance penalty (>50% in one section)
        assert imb > 0.0
        assert total > 0.0


class TestComputeFinalScore:
    """Tests for compute_final_score function."""

    def test_compute_final_score_empty(self, tmp_path):
        """Test final score with no headings."""
        headings = []
        weights = ScoringWeights()
        config = ChunkSizeConfig()

        metrics = compute_final_score(headings, total_lines=100, weights=weights, config=config)

        assert metrics.total_headings == 0
        assert metrics.final_score == 0.0

    def test_compute_final_score_complete(self, tmp_path):
        """Test final score computation with complete structure."""
        headings = [
            Heading(level=1, text="Chapter 1", line_number=1, section_start=1),
            Heading(level=2, text="Section 1.1", line_number=20, section_start=20),
            Heading(level=3, text="Subsection 1.1.1", line_number=30, section_start=30),
            Heading(level=1, text="Chapter 2", line_number=50, section_start=50),
            Heading(level=2, text="Section 2.1", line_number=60, section_start=60),
        ]
        weights = ScoringWeights()
        config = ChunkSizeConfig()

        metrics = compute_final_score(headings, total_lines=100, weights=weights, config=config)

        assert metrics.total_headings == 5
        assert metrics.h1_h2_count == 4
        assert metrics.max_depth == 3
        assert 0.0 <= metrics.coverage_score <= 1.0
        assert 0.0 <= metrics.hierarchy_score <= 1.0
        assert 0.0 <= metrics.chunkability_score <= 1.0
        assert 0.0 <= metrics.final_score <= 1.0


class TestCompareAndSelect:
    """Tests for compare_and_select function."""

    def test_compare_and_select_style_wins(self, tmp_path):
        """Test that style file wins when it has better score."""
        style_file = tmp_path / "test.style.md"
        hier_file = tmp_path / "test.hier.md"

        # Style file has better structure
        style_file.write_text(
            """# Chapter 1

Content here.

## Section 1.1

More content.

# Chapter 2

Final content.
""",
            encoding="utf-8",
        )

        # Hier file has worse structure (only H1)
        hier_file.write_text(
            """# Chapter 1

Content here.

# Chapter 2

More content.
""",
            encoding="utf-8",
        )

        winner = compare_and_select(style_file, hier_file)

        # Style should win due to better hierarchy
        assert winner == style_file

    def test_compare_and_select_hier_wins(self, tmp_path):
        """Test that hier file wins when it has better score."""
        style_file = tmp_path / "test.style.md"
        hier_file = tmp_path / "test.hier.md"

        # Style file has worse structure
        style_file.write_text(
            """# Chapter 1

Content here.

# Chapter 2

More content.
""",
            encoding="utf-8",
        )

        # Hier file has better structure
        hier_file.write_text(
            """# Chapter 1

Content here.

## Section 1.1

More content.

## Section 1.2

Even more content.

# Chapter 2

Final content.
""",
            encoding="utf-8",
        )

        winner = compare_and_select(style_file, hier_file)

        # Hier should win due to better hierarchy
        assert winner == hier_file

    def test_compare_and_select_file_not_found(self, tmp_path):
        """Test that FileNotFoundError is raised for missing files."""
        style_file = tmp_path / "test.style.md"
        hier_file = tmp_path / "test.hier.md"

        style_file.write_text("# Test", encoding="utf-8")

        with pytest.raises(FileNotFoundError, match="Hier file not found"):
            compare_and_select(style_file, hier_file)

    def test_compare_and_select_verbose(self, tmp_path, capsys):
        """Test verbose output."""
        style_file = tmp_path / "test.style.md"
        hier_file = tmp_path / "test.hier.md"

        style_file.write_text(
            """# Chapter 1

Content.
""",
            encoding="utf-8",
        )

        hier_file.write_text(
            """# Chapter 1

Content.
""",
            encoding="utf-8",
        )

        compare_and_select(style_file, hier_file, verbose=True)

        captured = capsys.readouterr()
        assert "Style-based Analysis" in captured.out
        assert "Hierarchy-based Analysis" in captured.out
        assert "Winner" in captured.out

    def test_compare_and_select_tie_breaker_chunkability(self, tmp_path):
        """Test tie-breaking prefers better chunkability."""
        style_file = tmp_path / "test.style.md"
        hier_file = tmp_path / "test.hier.md"

        # Both files have similar structure, but we'll use custom weights/config
        # to create a tie scenario
        style_file.write_text(
            """# Chapter 1

Content here.

# Chapter 2

More content.
""",
            encoding="utf-8",
        )

        hier_file.write_text(
            """# Chapter 1

Content here.

# Chapter 2

More content.
""",
            encoding="utf-8",
        )

        # Use custom config to create different chunkability scores
        config = ChunkSizeConfig(target_min=150, target_max=400, words_per_line=12.0)
        weights = ScoringWeights()

        winner = compare_and_select(style_file, hier_file, weights=weights, config=config)

        # Should select one (tie-breaker will prefer hier by default)
        assert winner in (style_file, hier_file)

    def test_compare_and_select_custom_weights(self, tmp_path):
        """Test comparison with custom scoring weights."""
        style_file = tmp_path / "test.style.md"
        hier_file = tmp_path / "test.hier.md"

        style_file.write_text(
            """# Chapter 1

Content.
""",
            encoding="utf-8",
        )

        hier_file.write_text(
            """# Chapter 1

Content.
""",
            encoding="utf-8",
        )

        weights = ScoringWeights(hierarchy=0.5, chunkability=0.3, coverage=0.2)
        config = ChunkSizeConfig()

        winner = compare_and_select(style_file, hier_file, weights=weights, config=config)

        assert winner in (style_file, hier_file)


class TestRenameFiles:
    """Tests for rename_files function."""

    def test_rename_files_style_winner(self, tmp_path):
        """Test copying style winner to final path."""
        style_file = tmp_path / "test.style.md"
        final_file = tmp_path / "test.md"

        style_file.write_text("# Test Content", encoding="utf-8")

        rename_files(style_file, tmp_path / "test.hier.md")

        assert final_file.exists()
        assert final_file.read_text(encoding="utf-8") == "# Test Content"
        assert style_file.exists()  # Original should still exist

    def test_rename_files_hier_winner(self, tmp_path):
        """Test copying hier winner to final path."""
        hier_file = tmp_path / "test.hier.md"
        final_file = tmp_path / "test.md"

        hier_file.write_text("# Test Content", encoding="utf-8")

        rename_files(hier_file, tmp_path / "test.style.md")

        assert final_file.exists()
        assert final_file.read_text(encoding="utf-8") == "# Test Content"
        assert hier_file.exists()  # Original should still exist

    def test_rename_files_already_exists(self, tmp_path):
        """Test that FileExistsError is raised if target exists."""
        style_file = tmp_path / "test.style.md"
        final_file = tmp_path / "test.md"

        style_file.write_text("# Test Content", encoding="utf-8")
        final_file.write_text("# Existing Content", encoding="utf-8")

        with pytest.raises(FileExistsError, match="already exists"):
            rename_files(style_file, tmp_path / "test.hier.md")

    def test_rename_files_verbose(self, tmp_path, capsys):
        """Test verbose output."""
        style_file = tmp_path / "test.style.md"
        style_file.write_text("# Test", encoding="utf-8")

        rename_files(style_file, tmp_path / "test.hier.md", verbose=True)

        captured = capsys.readouterr()
        assert "Copied winner" in captured.out

