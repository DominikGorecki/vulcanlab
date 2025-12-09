"""
Unit tests for chunk headings module.

Tests heading detection, parsing, hierarchy assignment, chunk boundary detection,
and edge cases for the chunk_headings module.

Usage:
    pytest tests/unit/test_chunk_headings.py -v
"""

import pytest
from unittest.mock import Mock, MagicMock, patch
from pathlib import Path
from tempfile import TemporaryDirectory
import json

from vulcanlab.chunking.chunk_headings import (
    _parse_suggestions,
    _parse_headings,
    _calculate_heading_ranges,
    _get_content_for_range,
    chunk_headings,
)
from vulcanlab.sanitization.extract_titles import HashMismatchError


class TestParseSuggestions:
    """Tests for _parse_suggestions() function."""

    def test_parse_suggestions_success(self):
        """Test parsing suggestions file successfully."""
        with TemporaryDirectory() as tmpdir:
            suggestions_path = Path(tmpdir) / "suggestions.vec_sugg.md"
            suggestions_path.write_text("""
Some text before

```
10: VECTORIZE
15: SKIP
20: VECTORIZE
25: SKIP
```

Some text after
""", encoding='utf-8')
            
            decisions = _parse_suggestions(suggestions_path)
            
            assert decisions[10] == "VECTORIZE"
            assert decisions[15] == "SKIP"
            assert decisions[20] == "VECTORIZE"
            assert decisions[25] == "SKIP"
            assert len(decisions) == 4

    def test_parse_suggestions_case_insensitive(self):
        """Test that suggestions parsing is case insensitive."""
        with TemporaryDirectory() as tmpdir:
            suggestions_path = Path(tmpdir) / "suggestions.vec_sugg.md"
            suggestions_path.write_text("""
```
10: vectorize
15: skip
20: VECTORIZE
25: Skip
```
""", encoding='utf-8')
            
            decisions = _parse_suggestions(suggestions_path)
            
            assert decisions[10] == "VECTORIZE"
            assert decisions[15] == "SKIP"
            assert decisions[20] == "VECTORIZE"
            assert decisions[25] == "SKIP"

    def test_parse_suggestions_no_code_block(self):
        """Test parsing when file has no code block."""
        with TemporaryDirectory() as tmpdir:
            suggestions_path = Path(tmpdir) / "suggestions.vec_sugg.md"
            suggestions_path.write_text("Just some text without code blocks", encoding='utf-8')
            
            decisions = _parse_suggestions(suggestions_path)
            
            assert decisions == {}

    def test_parse_suggestions_empty_code_block(self):
        """Test parsing when code block is empty."""
        with TemporaryDirectory() as tmpdir:
            suggestions_path = Path(tmpdir) / "suggestions.vec_sugg.md"
            suggestions_path.write_text("```\n\n```", encoding='utf-8')
            
            decisions = _parse_suggestions(suggestions_path)
            
            assert decisions == {}

    def test_parse_suggestions_malformed_lines(self):
        """Test parsing with malformed lines (should skip them)."""
        with TemporaryDirectory() as tmpdir:
            suggestions_path = Path(tmpdir) / "suggestions.vec_sugg.md"
            suggestions_path.write_text("""
```
10: VECTORIZE
invalid line
15: SKIP
another invalid
20: VECTORIZE
```
""", encoding='utf-8')
            
            decisions = _parse_suggestions(suggestions_path)
            
            assert decisions[10] == "VECTORIZE"
            assert decisions[15] == "SKIP"
            assert decisions[20] == "VECTORIZE"
            assert len(decisions) == 3

    def test_parse_suggestions_whitespace_handling(self):
        """Test parsing handles whitespace correctly."""
        with TemporaryDirectory() as tmpdir:
            suggestions_path = Path(tmpdir) / "suggestions.vec_sugg.md"
            suggestions_path.write_text("""
```
10:   VECTORIZE  
15:  SKIP  
```
""", encoding='utf-8')
            
            decisions = _parse_suggestions(suggestions_path)
            
            assert decisions[10] == "VECTORIZE"
            assert decisions[15] == "SKIP"


class TestParseHeadings:
    """Tests for _parse_headings() function."""

    def test_parse_headings_all_levels(self):
        """Test parsing headings at all levels (H1-H5)."""
        content = """# H1 Heading
Some content
## H2 Heading
More content
### H3 Heading
Even more
#### H4 Heading
Content
##### H5 Heading
Final content
"""
        headings = _parse_headings(content)
        
        assert len(headings) == 5
        assert headings[0] == (1, 1, "# H1 Heading")
        assert headings[1] == (3, 2, "## H2 Heading")
        assert headings[2] == (5, 3, "### H3 Heading")
        assert headings[3] == (7, 4, "#### H4 Heading")
        assert headings[4] == (9, 5, "##### H5 Heading")

    def test_parse_headings_skips_h6_and_above(self):
        """Test that headings H6 and above are skipped."""
        content = """# H1
## H2
### H3
#### H4
##### H5
###### H6 (should be skipped)
####### H7 (should be skipped)
"""
        headings = _parse_headings(content)
        
        assert len(headings) == 5
        assert all(level <= 5 for _, level, _ in headings)

    def test_parse_headings_no_headings(self):
        """Test parsing content with no headings."""
        content = """Just some regular content
with no headings at all.
"""
        headings = _parse_headings(content)
        
        assert headings == []

    def test_parse_headings_with_whitespace(self):
        """Test parsing headings with various whitespace."""
        content = """#   Heading with spaces
## Heading with space
###  Multiple   spaces
"""
        headings = _parse_headings(content)
        
        assert len(headings) == 3
        assert headings[0][2] == "#   Heading with spaces"
        assert headings[1][2] == "## Heading with space"
        assert headings[2][2] == "###  Multiple   spaces"

    def test_parse_headings_mixed_content(self):
        """Test parsing headings mixed with other content."""
        content = """Some intro text
# First Heading
Content here
## Second Heading
More content
Regular paragraph
### Third Heading
Final content
"""
        headings = _parse_headings(content)
        
        assert len(headings) == 3
        assert headings[0][1] == 1
        assert headings[1][1] == 2
        assert headings[2][1] == 3

    def test_parse_headings_not_at_start_of_line(self):
        """Test that headings not at start of line are not parsed."""
        content = """Some text # Not a heading
# Real heading
  # Indented, not a heading
"""
        headings = _parse_headings(content)
        
        assert len(headings) == 1
        assert headings[0][2] == "# Real heading"

    def test_parse_headings_empty_heading_text(self):
        """Test parsing headings with empty text (requires space after #)."""
        content = """# 
## 
###  
"""
        headings = _parse_headings(content)
        
        assert len(headings) == 3
        assert headings[0][2] == "# "
        assert headings[1][2] == "## "
        assert headings[2][2] == "###  "


class TestCalculateHeadingRanges:
    """Tests for _calculate_heading_ranges() function."""

    def test_calculate_ranges_simple(self):
        """Test calculating ranges for simple heading structure."""
        headings = [
            (1, 1, "# H1"),
            (5, 2, "## H2"),
            (10, 2, "## H2"),
        ]
        total_lines = 15
        
        ranges = _calculate_heading_ranges(headings, total_lines)
        
        assert len(ranges) == 3
        # First H1: ends when finds H2 (level 2 <= 1 is False, but H2 is level 2 which is > 1)
        # Actually, the code checks `if next_level <= level`, so H2 (level 2) <= H1 (level 1) is False
        # So H1 continues until end or finds another H1
        # Since there's no other H1, H1 goes to end
        assert ranges[0] == (1, 1, 1, 15)
        # First H2: ends before next H2 (level 2 <= 2 is True)
        assert ranges[1] == (5, 2, 5, 9)
        # Last H2: from line 10 to end
        assert ranges[2] == (10, 2, 10, 15)

    def test_calculate_ranges_nested(self):
        """Test calculating ranges for nested headings."""
        headings = [
            (1, 1, "# H1"),
            (5, 2, "## H2"),
            (8, 3, "### H3"),
            (12, 3, "### H3"),
            (15, 2, "## H2"),
        ]
        total_lines = 20
        
        ranges = _calculate_heading_ranges(headings, total_lines)
        
        # H1: no other H1 found, so goes to end
        assert ranges[0] == (1, 1, 1, 20)
        # H2: ends before next H2 at line 15 (level 2 <= 2)
        assert ranges[1] == (5, 2, 5, 14)
        # H3: ends before next H3 at line 12 (level 3 <= 3)
        assert ranges[2] == (8, 3, 8, 11)
        # H3: ends before next H2 at line 15 (level 2 <= 3 is True)
        assert ranges[3] == (12, 3, 12, 14)
        # Last H2: goes to end
        assert ranges[4] == (15, 2, 15, 20)

    def test_calculate_ranges_single_heading(self):
        """Test calculating range for single heading."""
        headings = [(1, 1, "# Only Heading")]
        total_lines = 10
        
        ranges = _calculate_heading_ranges(headings, total_lines)
        
        assert len(ranges) == 1
        assert ranges[0] == (1, 1, 1, 10)

    def test_calculate_ranges_same_level(self):
        """Test calculating ranges for headings at same level."""
        headings = [
            (1, 2, "## H2-1"),
            (5, 2, "## H2-2"),
            (10, 2, "## H2-3"),
        ]
        total_lines = 15
        
        ranges = _calculate_heading_ranges(headings, total_lines)
        
        assert ranges[0] == (1, 2, 1, 4)  # Ends before next H2
        assert ranges[1] == (5, 2, 5, 9)  # Ends before next H2
        assert ranges[2] == (10, 2, 10, 15)  # Last one goes to end

    def test_calculate_ranges_deeper_does_not_end(self):
        """Test that deeper headings don't end parent ranges."""
        headings = [
            (1, 1, "# H1"),
            (5, 2, "## H2"),
            (8, 3, "### H3"),
            (12, 4, "#### H4"),
        ]
        total_lines = 15
        
        ranges = _calculate_heading_ranges(headings, total_lines)
        
        # H1: no other H1 found, so goes to end
        # H2 (level 2) > H1 (level 1), so H2 doesn't end H1
        assert ranges[0] == (1, 1, 1, 15)
        # H2: no other H2 found, so goes to end
        # H3 (level 3) > H2 (level 2), so H3 doesn't end H2
        assert ranges[1] == (5, 2, 5, 15)
        # H3: no other H3 found, so goes to end
        # H4 (level 4) > H3 (level 3), so H4 doesn't end H3
        assert ranges[2] == (8, 3, 8, 15)
        # H4 is last, goes to end
        assert ranges[3] == (12, 4, 12, 15)


class TestGetContentForRange:
    """Tests for _get_content_for_range() function."""

    def test_get_content_for_range(self):
        """Test extracting content for a line range."""
        lines = ["Line 1", "Line 2", "Line 3", "Line 4", "Line 5"]
        
        content = _get_content_for_range(lines, start=2, end=4)
        
        assert content == "Line 2\nLine 3\nLine 4"

    def test_get_content_for_range_single_line(self):
        """Test extracting content for single line."""
        lines = ["Line 1", "Line 2", "Line 3"]
        
        content = _get_content_for_range(lines, start=2, end=2)
        
        assert content == "Line 2"

    def test_get_content_for_range_first_line(self):
        """Test extracting content starting from first line."""
        lines = ["Line 1", "Line 2", "Line 3"]
        
        content = _get_content_for_range(lines, start=1, end=2)
        
        assert content == "Line 1\nLine 2"

    def test_get_content_for_range_to_end(self):
        """Test extracting content to end of file."""
        lines = ["Line 1", "Line 2", "Line 3"]
        
        content = _get_content_for_range(lines, start=2, end=3)
        
        assert content == "Line 2\nLine 3"

    def test_get_content_for_range_all_lines(self):
        """Test extracting all lines."""
        lines = ["Line 1", "Line 2", "Line 3"]
        
        content = _get_content_for_range(lines, start=1, end=3)
        
        assert content == "Line 1\nLine 2\nLine 3"


class TestChunkHeadings:
    """Tests for chunk_headings() function."""

    @pytest.fixture
    def mock_work(self):
        """Create a mock Work object."""
        work = Mock()
        work.id = 1
        work.title = "Test Work"
        work.files = {
            "sanitized": {
                "path": "/tmp/sanitized.md",
                "hash": "test_hash_sanitized"
            },
            "vec_suggestions": {
                "path": "/tmp/suggestions.vec_sugg.md",
                "hash": "test_hash_suggestions"
            }
        }
        work.processing_status = {}
        return work

    @patch('vulcanlab.chunking.chunk_headings.compute_file_hash')
    @patch('vulcanlab.chunking.chunk_headings.get_session')
    def test_chunk_headings_success(
        self, mock_get_session, mock_compute_hash, mock_work
    ):
        """Test successful chunk creation."""
        # Setup session
        mock_session = MagicMock()
        mock_session.query.return_value.filter.return_value.first.return_value = mock_work
        mock_get_session.return_value.__enter__.return_value = mock_session

        # Setup file hashes
        mock_compute_hash.side_effect = ["test_hash_sanitized", "test_hash_suggestions"]

        # Create temporary files
        with TemporaryDirectory() as tmpdir:
            sanitized_path = Path(tmpdir) / "sanitized.md"
            suggestions_path = Path(tmpdir) / "suggestions.vec_sugg.md"
            
            sanitized_path.write_text("""# Chapter 1
Content for chapter 1
## Section 1.1
Content for section 1.1
## Section 1.2
Content for section 1.2
""", encoding='utf-8')
            
            suggestions_path.write_text("""
```
1: VECTORIZE
3: VECTORIZE
5: SKIP
```
""", encoding='utf-8')
            
            mock_work.files["sanitized"]["path"] = str(sanitized_path)
            mock_work.files["vec_suggestions"]["path"] = str(suggestions_path)

            result = chunk_headings(work_id=1, verbose=False)

            assert result == 2  # Two headings marked VECTORIZE
            # Work is also added to update processing_status, so 3 total adds
            assert mock_session.add.call_count == 3
            mock_session.commit.assert_called()

    @patch('vulcanlab.chunking.chunk_headings.get_session')
    def test_chunk_headings_work_not_found(self, mock_get_session):
        """Test error when work is not found."""
        mock_session = MagicMock()
        mock_session.query.return_value.filter.return_value.first.return_value = None
        mock_get_session.return_value.__enter__.return_value = mock_session

        with pytest.raises(ValueError, match="Work with ID 1 not found"):
            chunk_headings(work_id=1)

    @patch('vulcanlab.chunking.chunk_headings.get_session')
    def test_chunk_headings_no_files_metadata(self, mock_get_session, mock_work):
        """Test error when work has no files metadata."""
        mock_work.files = None
        mock_session = MagicMock()
        mock_session.query.return_value.filter.return_value.first.return_value = mock_work
        mock_get_session.return_value.__enter__.return_value = mock_session

        with pytest.raises(ValueError, match="has no files metadata"):
            chunk_headings(work_id=1)

    @patch('vulcanlab.chunking.chunk_headings.get_session')
    def test_chunk_headings_missing_sanitized(self, mock_get_session, mock_work):
        """Test error when sanitized file is missing."""
        del mock_work.files["sanitized"]
        mock_session = MagicMock()
        mock_session.query.return_value.filter.return_value.first.return_value = mock_work
        mock_get_session.return_value.__enter__.return_value = mock_session

        with pytest.raises(ValueError, match="does not have 'sanitized'"):
            chunk_headings(work_id=1)

    @patch('vulcanlab.chunking.chunk_headings.get_session')
    def test_chunk_headings_missing_vec_suggestions(self, mock_get_session, mock_work):
        """Test error when vec_suggestions file is missing."""
        del mock_work.files["vec_suggestions"]
        mock_session = MagicMock()
        mock_session.query.return_value.filter.return_value.first.return_value = mock_work
        mock_get_session.return_value.__enter__.return_value = mock_session

        with pytest.raises(ValueError, match="does not have 'vec_suggestions'"):
            chunk_headings(work_id=1)

    @patch('vulcanlab.chunking.chunk_headings.get_session')
    def test_chunk_headings_file_not_found_sanitized(self, mock_get_session, mock_work):
        """Test error when sanitized file doesn't exist on disk."""
        mock_session = MagicMock()
        mock_session.query.return_value.filter.return_value.first.return_value = mock_work
        mock_get_session.return_value.__enter__.return_value = mock_session

        mock_work.files["sanitized"]["path"] = "/nonexistent/file.md"

        with pytest.raises(FileNotFoundError, match="Sanitized file not found"):
            chunk_headings(work_id=1)

    @patch('vulcanlab.chunking.chunk_headings.compute_file_hash')
    @patch('vulcanlab.chunking.chunk_headings.get_session')
    def test_chunk_headings_hash_mismatch_sanitized(
        self, mock_get_session, mock_compute_hash, mock_work
    ):
        """Test error when sanitized file hash doesn't match."""
        mock_session = MagicMock()
        mock_session.query.return_value.filter.return_value.first.return_value = mock_work
        mock_get_session.return_value.__enter__.return_value = mock_session

        with TemporaryDirectory() as tmpdir:
            sanitized_path = Path(tmpdir) / "sanitized.md"
            suggestions_path = Path(tmpdir) / "suggestions.vec_sugg.md"
            
            sanitized_path.write_text("Content", encoding='utf-8')
            suggestions_path.write_text("```\n1: VECTORIZE\n```", encoding='utf-8')
            
            mock_work.files["sanitized"]["path"] = str(sanitized_path)
            mock_work.files["vec_suggestions"]["path"] = str(suggestions_path)

            # Hash mismatch for sanitized file
            mock_compute_hash.side_effect = ["different_hash", "test_hash_suggestions"]

            with pytest.raises(HashMismatchError):
                chunk_headings(work_id=1)

    @patch('vulcanlab.chunking.chunk_headings.compute_file_hash')
    @patch('vulcanlab.chunking.chunk_headings.get_session')
    def test_chunk_headings_hash_mismatch_suggestions(
        self, mock_get_session, mock_compute_hash, mock_work
    ):
        """Test error when suggestions file hash doesn't match."""
        mock_session = MagicMock()
        mock_session.query.return_value.filter.return_value.first.return_value = mock_work
        mock_get_session.return_value.__enter__.return_value = mock_session

        with TemporaryDirectory() as tmpdir:
            sanitized_path = Path(tmpdir) / "sanitized.md"
            suggestions_path = Path(tmpdir) / "suggestions.vec_sugg.md"
            
            sanitized_path.write_text("# Heading", encoding='utf-8')
            suggestions_path.write_text("```\n1: VECTORIZE\n```", encoding='utf-8')
            
            mock_work.files["sanitized"]["path"] = str(sanitized_path)
            mock_work.files["vec_suggestions"]["path"] = str(suggestions_path)

            # First hash matches, second doesn't
            mock_compute_hash.side_effect = ["test_hash_sanitized", "different_hash"]

            with pytest.raises(HashMismatchError):
                chunk_headings(work_id=1)

    @patch('vulcanlab.chunking.chunk_headings.compute_file_hash')
    @patch('vulcanlab.chunking.chunk_headings.get_session')
    def test_chunk_headings_no_headings(
        self, mock_get_session, mock_compute_hash, mock_work
    ):
        """Test chunking when document has no headings."""
        mock_session = MagicMock()
        mock_session.query.return_value.filter.return_value.first.return_value = mock_work
        mock_get_session.return_value.__enter__.return_value = mock_session

        mock_compute_hash.side_effect = ["test_hash_sanitized", "test_hash_suggestions"]

        with TemporaryDirectory() as tmpdir:
            sanitized_path = Path(tmpdir) / "sanitized.md"
            suggestions_path = Path(tmpdir) / "suggestions.vec_sugg.md"
            
            sanitized_path.write_text("Just regular content\nwith no headings", encoding='utf-8')
            suggestions_path.write_text("```\n1: VECTORIZE\n```", encoding='utf-8')
            
            mock_work.files["sanitized"]["path"] = str(sanitized_path)
            mock_work.files["vec_suggestions"]["path"] = str(suggestions_path)

            result = chunk_headings(work_id=1)

            assert result == 0
            # Work is still added to update processing_status
            from vulcanlab.data.models import Chunk
            chunk_calls = [call for call in mock_session.add.call_args_list 
                          if isinstance(call[0][0], Chunk)]
            assert len(chunk_calls) == 0

    @patch('vulcanlab.chunking.chunk_headings.compute_file_hash')
    @patch('vulcanlab.chunking.chunk_headings.get_session')
    def test_chunk_headings_no_vectorize_headings(
        self, mock_get_session, mock_compute_hash, mock_work
    ):
        """Test chunking when no headings are marked VECTORIZE."""
        mock_session = MagicMock()
        mock_session.query.return_value.filter.return_value.first.return_value = mock_work
        mock_get_session.return_value.__enter__.return_value = mock_session

        mock_compute_hash.side_effect = ["test_hash_sanitized", "test_hash_suggestions"]

        with TemporaryDirectory() as tmpdir:
            sanitized_path = Path(tmpdir) / "sanitized.md"
            suggestions_path = Path(tmpdir) / "suggestions.vec_sugg.md"
            
            sanitized_path.write_text("""# Heading 1
## Heading 2
""", encoding='utf-8')
            suggestions_path.write_text("""
```
1: SKIP
3: SKIP
```
""", encoding='utf-8')
            
            mock_work.files["sanitized"]["path"] = str(sanitized_path)
            mock_work.files["vec_suggestions"]["path"] = str(suggestions_path)

            result = chunk_headings(work_id=1)

            assert result == 0
            # Work is still added to update processing_status
            from vulcanlab.data.models import Chunk
            chunk_calls = [call for call in mock_session.add.call_args_list 
                          if isinstance(call[0][0], Chunk)]
            assert len(chunk_calls) == 0

    @patch('vulcanlab.chunking.chunk_headings.compute_file_hash')
    @patch('vulcanlab.chunking.chunk_headings.get_session')
    def test_chunk_headings_parent_child_relationship(
        self, mock_get_session, mock_compute_hash, mock_work
    ):
        """Test that parent-child relationships are correctly established."""
        mock_session = MagicMock()
        mock_session.query.return_value.filter.return_value.first.return_value = mock_work
        mock_get_session.return_value.__enter__.return_value = mock_session

        mock_compute_hash.side_effect = ["test_hash_sanitized", "test_hash_suggestions"]

        # Mock chunk IDs - need to track them properly
        chunk_ids = [1, 2]
        chunk_id_counter = [0]

        def mock_add(chunk):
            # Only assign ID to Chunk objects, not Work
            from vulcanlab.data.models import Chunk
            if isinstance(chunk, Chunk):
                chunk.id = chunk_ids[chunk_id_counter[0]]
                chunk_id_counter[0] += 1

        mock_session.add.side_effect = mock_add

        with TemporaryDirectory() as tmpdir:
            sanitized_path = Path(tmpdir) / "sanitized.md"
            suggestions_path = Path(tmpdir) / "suggestions.vec_sugg.md"
            
            sanitized_path.write_text("""# H1 Parent
Content
## H2 Child
Child content
""", encoding='utf-8')
            suggestions_path.write_text("""
```
1: VECTORIZE
3: VECTORIZE
```
""", encoding='utf-8')
            
            mock_work.files["sanitized"]["path"] = str(sanitized_path)
            mock_work.files["vec_suggestions"]["path"] = str(suggestions_path)

            result = chunk_headings(work_id=1)

            assert result == 2
            # Filter to only Chunk objects
            from vulcanlab.data.models import Chunk
            chunk_calls = [call for call in mock_session.add.call_args_list 
                          if isinstance(call[0][0], Chunk)]
            assert len(chunk_calls) == 2
            
            # Check that second chunk (H2) has parent_id set to first chunk (H1)
            h1_chunk = chunk_calls[0][0][0]
            h2_chunk = chunk_calls[1][0][0]
            
            assert h1_chunk.parent_id is None
            assert h2_chunk.parent_id == 1  # Parent is H1 chunk

    @patch('vulcanlab.chunking.chunk_headings.compute_file_hash')
    @patch('vulcanlab.chunking.chunk_headings.get_session')
    def test_chunk_headings_chunk_properties(
        self, mock_get_session, mock_compute_hash, mock_work
    ):
        """Test that chunks are created with correct properties."""
        mock_session = MagicMock()
        mock_session.query.return_value.filter.return_value.first.return_value = mock_work
        mock_get_session.return_value.__enter__.return_value = mock_session

        mock_compute_hash.side_effect = ["test_hash_sanitized", "test_hash_suggestions"]

        def mock_add(obj):
            from vulcanlab.data.models import Chunk
            if isinstance(obj, Chunk):
                obj.id = 1

        mock_session.add.side_effect = mock_add

        with TemporaryDirectory() as tmpdir:
            sanitized_path = Path(tmpdir) / "sanitized.md"
            suggestions_path = Path(tmpdir) / "suggestions.vec_sugg.md"
            
            sanitized_path.write_text("""# Heading
Content here
""", encoding='utf-8')
            suggestions_path.write_text("""
```
1: VECTORIZE
```
""", encoding='utf-8')
            
            mock_work.files["sanitized"]["path"] = str(sanitized_path)
            mock_work.files["vec_suggestions"]["path"] = str(suggestions_path)

            result = chunk_headings(work_id=1)

            assert result == 1
            # Find the Chunk object in add calls (work is also added)
            from vulcanlab.data.models import Chunk
            chunk_calls = [call for call in mock_session.add.call_args_list 
                          if isinstance(call[0][0], Chunk)]
            assert len(chunk_calls) == 1
            chunk = chunk_calls[0][0][0]
            assert chunk.work_id == 1
            assert chunk.level == "H1"
            assert chunk.start_line == 1
            assert chunk.end_line == 2
            assert chunk.vector_status == "no_vec"
            assert chunk.content == "# Heading\nContent here"

    @patch('vulcanlab.chunking.chunk_headings.compute_file_hash')
    @patch('vulcanlab.chunking.chunk_headings.get_session')
    def test_chunk_headings_updates_processing_status(
        self, mock_get_session, mock_compute_hash, mock_work
    ):
        """Test that processing_status is updated after chunking."""
        mock_session = MagicMock()
        mock_session.query.return_value.filter.return_value.first.return_value = mock_work
        mock_get_session.return_value.__enter__.return_value = mock_session

        mock_compute_hash.side_effect = ["test_hash_sanitized", "test_hash_suggestions"]

        def mock_add(obj):
            from vulcanlab.data.models import Chunk
            if isinstance(obj, Chunk):
                obj.id = 1

        mock_session.add.side_effect = mock_add

        with TemporaryDirectory() as tmpdir:
            sanitized_path = Path(tmpdir) / "sanitized.md"
            suggestions_path = Path(tmpdir) / "suggestions.vec_sugg.md"
            
            sanitized_path.write_text("# Heading", encoding='utf-8')
            suggestions_path.write_text("```\n1: VECTORIZE\n```", encoding='utf-8')
            
            mock_work.files["sanitized"]["path"] = str(sanitized_path)
            mock_work.files["vec_suggestions"]["path"] = str(suggestions_path)

            chunk_headings(work_id=1)

            # Check that processing_status was updated
            assert mock_work.processing_status["heading_chunks"] == "completed"
            # Work should be added to session for update
            work_add_calls = [call for call in mock_session.add.call_args_list 
                            if call[0][0] is mock_work]
            assert len(work_add_calls) == 1

    @patch('vulcanlab.chunking.chunk_headings.compute_file_hash')
    @patch('vulcanlab.chunking.chunk_headings.get_session')
    def test_chunk_headings_multiple_nested_levels(
        self, mock_get_session, mock_compute_hash, mock_work
    ):
        """Test chunking with multiple nested heading levels."""
        mock_session = MagicMock()
        mock_session.query.return_value.filter.return_value.first.return_value = mock_work
        mock_get_session.return_value.__enter__.return_value = mock_session

        mock_compute_hash.side_effect = ["test_hash_sanitized", "test_hash_suggestions"]

        chunk_ids = [1, 2, 3, 4]
        chunk_id_counter = [0]

        def mock_add(obj):
            from vulcanlab.data.models import Chunk
            if isinstance(obj, Chunk):
                obj.id = chunk_ids[chunk_id_counter[0]]
                chunk_id_counter[0] += 1

        mock_session.add.side_effect = mock_add

        with TemporaryDirectory() as tmpdir:
            sanitized_path = Path(tmpdir) / "sanitized.md"
            suggestions_path = Path(tmpdir) / "suggestions.vec_sugg.md"
            
            sanitized_path.write_text("""# H1
Content
## H2-1
Content
### H3-1
Content
## H2-2
Content
""", encoding='utf-8')
            suggestions_path.write_text("""
```
1: VECTORIZE
3: VECTORIZE
5: VECTORIZE
7: VECTORIZE
```
""", encoding='utf-8')
            
            mock_work.files["sanitized"]["path"] = str(sanitized_path)
            mock_work.files["vec_suggestions"]["path"] = str(suggestions_path)

            result = chunk_headings(work_id=1)

            assert result == 4
            from vulcanlab.data.models import Chunk
            chunk_calls = [call for call in mock_session.add.call_args_list 
                          if isinstance(call[0][0], Chunk)]
            assert len(chunk_calls) == 4
            
            # Check parent relationships
            h1_chunk = chunk_calls[0][0][0]
            h2_1_chunk = chunk_calls[1][0][0]
            h3_chunk = chunk_calls[2][0][0]
            h2_2_chunk = chunk_calls[3][0][0]
            
            assert h1_chunk.parent_id is None
            assert h2_1_chunk.parent_id == 1  # Parent is H1
            assert h3_chunk.parent_id == 2  # Parent is H2-1
            assert h2_2_chunk.parent_id == 1  # Parent is H1 (not H3)

    @patch('vulcanlab.chunking.chunk_headings.compute_file_hash')
    @patch('vulcanlab.chunking.chunk_headings.get_session')
    def test_chunk_headings_parent_not_vectorized(
        self, mock_get_session, mock_compute_hash, mock_work
    ):
        """Test that child headings can still be chunked even if parent is not vectorized."""
        mock_session = MagicMock()
        mock_session.query.return_value.filter.return_value.first.return_value = mock_work
        mock_get_session.return_value.__enter__.return_value = mock_session

        mock_compute_hash.side_effect = ["test_hash_sanitized", "test_hash_suggestions"]

        def mock_add(obj):
            from vulcanlab.data.models import Chunk
            if isinstance(obj, Chunk):
                obj.id = 1

        mock_session.add.side_effect = mock_add

        with TemporaryDirectory() as tmpdir:
            sanitized_path = Path(tmpdir) / "sanitized.md"
            suggestions_path = Path(tmpdir) / "suggestions.vec_sugg.md"
            
            sanitized_path.write_text("""# H1 Parent
Content
## H2 Child
Child content
""", encoding='utf-8')
            suggestions_path.write_text("""
```
1: SKIP
3: VECTORIZE
```
""", encoding='utf-8')
            
            mock_work.files["sanitized"]["path"] = str(sanitized_path)
            mock_work.files["vec_suggestions"]["path"] = str(suggestions_path)

            result = chunk_headings(work_id=1)

            assert result == 1
            from vulcanlab.data.models import Chunk
            chunk_calls = [call for call in mock_session.add.call_args_list 
                          if isinstance(call[0][0], Chunk)]
            assert len(chunk_calls) == 1
            
            # H2 child should have no parent since H1 was not vectorized
            h2_chunk = chunk_calls[0][0][0]
            assert h2_chunk.parent_id is None

    @patch('vulcanlab.chunking.chunk_headings.compute_file_hash')
    @patch('vulcanlab.chunking.chunk_headings.get_session')
    def test_chunk_headings_skips_h6_and_above(
        self, mock_get_session, mock_compute_hash, mock_work
    ):
        """Test that H6 and above headings are skipped."""
        mock_session = MagicMock()
        mock_session.query.return_value.filter.return_value.first.return_value = mock_work
        mock_get_session.return_value.__enter__.return_value = mock_session

        mock_compute_hash.side_effect = ["test_hash_sanitized", "test_hash_suggestions"]

        def mock_add(obj):
            from vulcanlab.data.models import Chunk
            if isinstance(obj, Chunk):
                obj.id = 1

        mock_session.add.side_effect = mock_add

        with TemporaryDirectory() as tmpdir:
            sanitized_path = Path(tmpdir) / "sanitized.md"
            suggestions_path = Path(tmpdir) / "suggestions.vec_sugg.md"
            
            sanitized_path.write_text("""# H1
## H2
### H3
#### H4
##### H5
###### H6 (should be skipped)
####### H7 (should be skipped)
""", encoding='utf-8')
            suggestions_path.write_text("""
```
1: VECTORIZE
2: VECTORIZE
3: VECTORIZE
4: VECTORIZE
5: VECTORIZE
6: VECTORIZE
7: VECTORIZE
```
""", encoding='utf-8')
            
            mock_work.files["sanitized"]["path"] = str(sanitized_path)
            mock_work.files["vec_suggestions"]["path"] = str(suggestions_path)

            result = chunk_headings(work_id=1)

            # Only H1-H5 should be chunked
            assert result == 5
            from vulcanlab.data.models import Chunk
            chunk_calls = [call for call in mock_session.add.call_args_list 
                          if isinstance(call[0][0], Chunk)]
            assert len(chunk_calls) == 5
            # Verify all chunks are H1-H5
            assert all(chunk.level in ["H1", "H2", "H3", "H4", "H5"] 
                      for chunk in [call[0][0] for call in chunk_calls])

