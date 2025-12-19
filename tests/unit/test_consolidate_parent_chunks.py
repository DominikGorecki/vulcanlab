"""
Unit tests for consolidation using parent chunks.

Tests the refactored consolidation logic that uses parent chunk content
instead of local markdown files.
"""

import pytest
from unittest.mock import Mock, MagicMock
from vulcanlab.augmentation.consolidate_context import (
    _extract_content_from_parent,
    _calculate_coverage,
    _merge_adjacent_items,
    _finalize_group
)


class TestExtractContentFromParent:
    """Tests for extracting content from parent chunks."""

    def test_extract_content_basic(self):
        """Test basic content extraction from parent chunk."""
        parent = Mock()
        parent.content = "Line 1\nLine 2\nLine 3\nLine 4\nLine 5"

        result = _extract_content_from_parent(parent, start_line=2, end_line=4)
        assert result == "Line 2\nLine 3\nLine 4"

    def test_extract_content_single_line(self):
        """Test extracting a single line."""
        parent = Mock()
        parent.content = "Line 1\nLine 2\nLine 3"

        result = _extract_content_from_parent(parent, start_line=2, end_line=2)
        assert result == "Line 2"

    def test_extract_content_full_range(self):
        """Test extracting entire parent content."""
        parent = Mock()
        parent.content = "Line 1\nLine 2\nLine 3"

        result = _extract_content_from_parent(parent, start_line=1, end_line=3)
        assert result == "Line 1\nLine 2\nLine 3"

    def test_extract_content_out_of_bounds_start(self):
        """Test clamping when start_line is before parent content."""
        parent = Mock()
        parent.content = "Line 1\nLine 2\nLine 3"

        # start_line=0 should be clamped to 1 (index 0)
        result = _extract_content_from_parent(parent, start_line=0, end_line=2)
        assert result == "Line 1\nLine 2"

    def test_extract_content_out_of_bounds_end(self):
        """Test clamping when end_line exceeds parent content."""
        parent = Mock()
        parent.content = "Line 1\nLine 2\nLine 3"

        # end_line=10 should be clamped to 3
        result = _extract_content_from_parent(parent, start_line=2, end_line=10)
        assert result == "Line 2\nLine 3"

    def test_extract_content_both_bounds_clamped(self):
        """Test clamping both start and end bounds."""
        parent = Mock()
        parent.content = "Line 1\nLine 2\nLine 3"

        result = _extract_content_from_parent(parent, start_line=-5, end_line=100)
        assert result == "Line 1\nLine 2\nLine 3"

    def test_extract_content_empty_parent(self):
        """Test handling empty parent content."""
        parent = Mock()
        parent.content = ""

        result = _extract_content_from_parent(parent, start_line=1, end_line=5)
        assert result == ""

    def test_extract_content_none_parent(self):
        """Test handling None parent."""
        result = _extract_content_from_parent(None, start_line=1, end_line=5)
        assert result == ""

    def test_extract_content_parent_no_content(self):
        """Test handling parent without content attribute."""
        parent = Mock()
        parent.content = None

        result = _extract_content_from_parent(parent, start_line=1, end_line=5)
        assert result == ""


class TestCalculateCoverage:
    """Tests for character-count-based coverage calculation."""

    def test_coverage_full(self):
        """Test coverage when children cover entire parent."""
        parent = Mock()
        parent.content = "This is a parent with 50 characters total text"  # 47 chars

        items = [
            {'content': "This is a parent with 50 characters total text"}
        ]

        coverage = _calculate_coverage(items, parent)
        assert coverage == 1.0

    def test_coverage_half(self):
        """Test coverage when children cover half of parent."""
        parent = Mock()
        parent.content = "1234567890"  # 10 chars

        items = [
            {'content': "12345"}  # 5 chars
        ]

        coverage = _calculate_coverage(items, parent)
        assert coverage == 0.5

    def test_coverage_multiple_children(self):
        """Test coverage with multiple child chunks."""
        parent = Mock()
        parent.content = "1234567890"  # 10 chars

        items = [
            {'content': "123"},  # 3 chars
            {'content': "45"},   # 2 chars
        ]

        coverage = _calculate_coverage(items, parent)
        assert coverage == 0.5

    def test_coverage_exceeds_parent(self):
        """Test coverage when children exceed parent (can happen with enrichment)."""
        parent = Mock()
        parent.content = "12345"  # 5 chars

        items = [
            {'content': "1234567890"}  # 10 chars
        ]

        coverage = _calculate_coverage(items, parent)
        assert coverage == 2.0

    def test_coverage_empty_parent(self):
        """Test coverage with empty parent content."""
        parent = Mock()
        parent.content = ""

        items = [
            {'content': "some content"}
        ]

        coverage = _calculate_coverage(items, parent)
        assert coverage == 0.0

    def test_coverage_none_parent(self):
        """Test coverage with None parent."""
        items = [
            {'content': "some content"}
        ]

        coverage = _calculate_coverage(items, None)
        assert coverage == 0.0

    def test_coverage_parent_no_content(self):
        """Test coverage with parent lacking content."""
        parent = Mock()
        parent.content = None

        items = [
            {'content': "some content"}
        ]

        coverage = _calculate_coverage(items, parent)
        assert coverage == 0.0

    def test_coverage_empty_children(self):
        """Test coverage when children have no content."""
        parent = Mock()
        parent.content = "some parent content"

        items = [
            {'content': ""},
            {'content': ""}
        ]

        coverage = _calculate_coverage(items, parent)
        assert coverage == 0.0

    def test_coverage_missing_content_field(self):
        """Test coverage when some items lack content field."""
        parent = Mock()
        parent.content = "1234567890"  # 10 chars

        items = [
            {'content': "12345"},  # 5 chars
            {}  # No content field
        ]

        coverage = _calculate_coverage(items, parent)
        assert coverage == 0.5


class TestMergeAdjacentItems:
    """Tests for merging adjacent items using parent chunks."""

    def test_merge_adjacent_with_parent_chunk(self):
        """Test merging adjacent items extracts correct content from parent."""
        parent = Mock()
        parent.content = "Line 1\nLine 2\nLine 3\nLine 4\nLine 5\nLine 6\nLine 7\nLine 8"

        items = [
            {
                'id': 1,
                'start_line': 2,
                'end_line': 3,
                'content': "Line 2\nLine 3",
                'work_id': 1,
                'parent_id': 10,
                'score': 0.9
            },
            {
                'id': 2,
                'start_line': 5,
                'end_line': 6,
                'content': "Line 5\nLine 6",
                'work_id': 1,
                'parent_id': 10,
                'score': 0.8
            }
        ]

        # Gap is 1 line (line 4), within default gap of 7
        merged = _merge_adjacent_items(items, parent, None, line_gap=7, enrich_from_md=True)

        assert len(merged) == 1
        assert merged[0]['start_line'] == 2
        assert merged[0]['end_line'] == 6
        # Should include the gap (line 4) between the two chunks
        assert "Line 2" in merged[0]['content']
        assert "Line 6" in merged[0]['content']

    def test_merge_gap_included(self):
        """Test that merged content includes gap between adjacent chunks."""
        parent = Mock()
        parent.content = "A\nB\nC\nD\nE"

        items = [
            {
                'id': 1,
                'start_line': 1,
                'end_line': 2,
                'content': "A\nB",
                'work_id': 1,
                'score': 0.9
            },
            {
                'id': 2,
                'start_line': 4,
                'end_line': 5,
                'content': "D\nE",
                'work_id': 1,
                'score': 0.8
            }
        ]

        merged = _merge_adjacent_items(items, parent, None, line_gap=7, enrich_from_md=True)

        assert len(merged) == 1
        # Should include line C (the gap)
        assert "C" in merged[0]['content']

    def test_no_merge_gap_too_large(self):
        """Test that items aren't merged when gap exceeds threshold."""
        parent = Mock()
        parent.content = "\n".join([f"Line {i}" for i in range(1, 21)])  # 20 lines

        items = [
            {
                'id': 1,
                'start_line': 1,
                'end_line': 2,
                'content': "Line 1\nLine 2",
                'work_id': 1,
                'score': 0.9
            },
            {
                'id': 2,
                'start_line': 15,
                'end_line': 16,
                'content': "Line 15\nLine 16",
                'work_id': 1,
                'score': 0.8
            }
        ]

        # Gap is 12 lines, exceeds line_gap of 7
        merged = _merge_adjacent_items(items, parent, None, line_gap=7, enrich_from_md=True)

        assert len(merged) == 2  # Not merged

    def test_merge_without_parent_uses_existing_content(self):
        """Test merging without parent concatenates existing content."""
        items = [
            {
                'id': 1,
                'start_line': 1,
                'end_line': 2,
                'content': "Content A",
                'work_id': 1,
                'score': 0.9
            },
            {
                'id': 2,
                'start_line': 3,
                'end_line': 4,
                'content': "Content B",
                'work_id': 1,
                'score': 0.8
            }
        ]

        merged = _merge_adjacent_items(items, None, None, line_gap=7, enrich_from_md=False)

        assert len(merged) == 1
        assert "Content A" in merged[0]['content']
        assert "Content B" in merged[0]['content']

    def test_merge_preserves_chunk_ids(self):
        """Test that merging preserves all chunk IDs."""
        parent = Mock()
        parent.content = "Line 1\nLine 2\nLine 3\nLine 4"

        items = [
            {
                'chunk_ids': [1, 2],
                'start_line': 1,
                'end_line': 2,
                'content': "Line 1\nLine 2",
                'work_id': 1,
                'score': 0.9
            },
            {
                'chunk_ids': [3],
                'start_line': 3,
                'end_line': 4,
                'content': "Line 3\nLine 4",
                'work_id': 1,
                'score': 0.8
            }
        ]

        merged = _merge_adjacent_items(items, parent, None, line_gap=7, enrich_from_md=True)

        assert len(merged) == 1
        assert merged[0]['chunk_ids'] == [1, 2, 3]

    def test_merge_uses_max_score(self):
        """Test that merged item uses maximum score from children."""
        parent = Mock()
        parent.content = "Line 1\nLine 2\nLine 3\nLine 4"

        items = [
            {
                'id': 1,
                'start_line': 1,
                'end_line': 2,
                'content': "Line 1\nLine 2",
                'work_id': 1,
                'score': 0.7
            },
            {
                'id': 2,
                'start_line': 3,
                'end_line': 4,
                'content': "Line 3\nLine 4",
                'work_id': 1,
                'score': 0.95
            }
        ]

        merged = _merge_adjacent_items(items, parent, None, line_gap=7, enrich_from_md=True)

        assert len(merged) == 1
        assert merged[0]['score'] == 0.95


class TestFinalizeGroup:
    """Tests for finalizing groups with heading preservation."""

    def test_heading_chain_preserved_from_breadcrumbs(self):
        """Test heading chain preserved from heading_breadcrumbs."""
        parent = Mock()
        parent.content = "## Section\n\nContent here"

        items = [
            {
                'id': 1,
                'start_line': 1,
                'end_line': 3,
                'content': "Content here",
                'work_id': 1,
                'score': 0.9,
                'level': 'chunk',
                'heading_breadcrumbs': 'Chapter 1 > Section A > Subsection B'
            }
        ]

        result = _finalize_group(items, parent, None, enrich_from_md=True)

        # Should prepend the last heading from breadcrumbs
        assert 'Subsection B' in result['content']

    def test_heading_chain_for_heading_chunk(self):
        """Test heading chain extraction for heading chunks."""
        parent = Mock()
        parent.content = "## My Heading\n\nSome content"

        items = [
            {
                'id': 1,
                'start_line': 1,
                'end_line': 3,
                'content': "## My Heading\n\nSome content",
                'work_id': 1,
                'score': 0.9,
                'level': 'H2',
                'heading_breadcrumbs': 'Chapter 1 > My Heading'
            }
        ]

        result = _finalize_group(items, parent, None, enrich_from_md=True)

        # Should preserve the heading with proper markdown
        assert '## My Heading' in result['content']

    def test_no_duplicate_headings(self):
        """Test that headings aren't duplicated if already in content."""
        parent = Mock()
        parent.content = "## Section\n\nContent"

        items = [
            {
                'id': 1,
                'start_line': 1,
                'end_line': 3,
                'content': "## Section\n\nContent",
                'work_id': 1,
                'score': 0.9,
                'level': 'H2',
                'heading_breadcrumbs': 'Chapter 1 > Section'
            }
        ]

        result = _finalize_group(items, parent, None, enrich_from_md=True)

        # Should not duplicate the heading
        content = result['content']
        # Count occurrences of "## Section"
        assert content.count('## Section') == 1

    def test_heading_breadcrumbs_as_list(self):
        """Test handling breadcrumbs as list format."""
        parent = Mock()
        parent.content = "Content"

        items = [
            {
                'id': 1,
                'start_line': 1,
                'end_line': 1,
                'content': "Content",
                'work_id': 1,
                'score': 0.9,
                'level': 'chunk',
                'heading_breadcrumbs': ['Chapter 1', 'Section A', 'Subsection B']
            }
        ]

        result = _finalize_group(items, parent, None, enrich_from_md=True)

        # Should use the last item from list
        assert 'Subsection B' in result['content']

    def test_no_heading_breadcrumbs(self):
        """Test handling items without heading_breadcrumbs."""
        parent = Mock()
        parent.content = "Just content"

        items = [
            {
                'id': 1,
                'start_line': 1,
                'end_line': 1,
                'content': "Just content",
                'work_id': 1,
                'score': 0.9,
                'level': 'chunk'
            }
        ]

        result = _finalize_group(items, parent, None, enrich_from_md=True)

        # Should just have the content without prepended heading
        assert result['content'] == "Just content"


class TestEdgeCases:
    """Tests for edge cases and error conditions."""

    def test_missing_parent_returns_original(self):
        """Test that missing parent chunk returns children as-is."""
        items = [
            {
                'id': 1,
                'start_line': 1,
                'end_line': 2,
                'content': "Content A",
                'work_id': 1,
                'score': 0.9
            },
            {
                'id': 2,
                'start_line': 10,
                'end_line': 11,
                'content': "Content B",
                'work_id': 1,
                'score': 0.8
            }
        ]

        # No parent provided, large gap, should not merge
        merged = _merge_adjacent_items(items, None, None, line_gap=5, enrich_from_md=False)

        assert len(merged) == 2

    def test_empty_parent_content_handled(self):
        """Test handling of parent with empty content."""
        parent = Mock()
        parent.content = ""

        items = [
            {
                'id': 1,
                'start_line': 1,
                'end_line': 2,
                'content': "Some content",
                'work_id': 1,
                'score': 0.9
            }
        ]

        # Should not crash, should return empty string for extraction
        result = _extract_content_from_parent(parent, 1, 2)
        assert result == ""

        # Coverage should be 0
        coverage = _calculate_coverage(items, parent)
        assert coverage == 0.0

    def test_groups_by_parent_id(self):
        """Test that items are correctly grouped by parent_id."""
        # This would be tested in integration, but verifying the concept
        parent1 = Mock()
        parent1.content = "Parent 1 content"

        parent2 = Mock()
        parent2.content = "Parent 2 content"

        items_p1 = [
            {
                'id': 1,
                'start_line': 1,
                'end_line': 2,
                'content': "Content",
                'work_id': 1,
                'parent_id': 10,
                'score': 0.9
            }
        ]

        items_p2 = [
            {
                'id': 2,
                'start_line': 1,
                'end_line': 2,
                'content': "Content",
                'work_id': 1,
                'parent_id': 20,
                'score': 0.8
            }
        ]

        # Each group should be processed separately
        merged1 = _merge_adjacent_items(items_p1, parent1, None, enrich_from_md=True)
        merged2 = _merge_adjacent_items(items_p2, parent2, None, enrich_from_md=True)

        assert len(merged1) == 1
        assert len(merged2) == 1
        assert merged1[0]['parent_id'] == 10
        assert merged2[0]['parent_id'] == 20
