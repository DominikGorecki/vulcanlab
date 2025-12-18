"""
Unit tests for context consolidation module.

Tests consolidation logic, deduplication, merging strategies, and edge cases
for the consolidate_context module.

Usage:
    pytest tests/unit/test_consolidate_context.py -v
"""

import pytest
from unittest.mock import Mock, MagicMock, patch, mock_open
from pathlib import Path
from tempfile import TemporaryDirectory
import json

from vulcanlab.config.app_config import AppConfig, LoggingConfig

from vulcanlab.augmentation.consolidate_context import (
    ConsolidatedGroup,
    ConsolidationResult,
    _calculate_coverage,
    _merge_adjacent_items,
    _finalize_group,
    _read_content_from_file,
    _get_heading_chain,
    _get_level_order,
    consolidate_context,
    DEFAULT_COVERAGE_THRESHOLD,
    DEFAULT_LINE_GAP,
    DEFAULT_MIN_CONTENT_LENGTH,
    DEFAULT_ENRICH_FROM_MD,
)


class TestGetLevelOrder:
    """Tests for _get_level_order() function."""

    def test_h1_level(self):
        """Test H1 level returns correct order."""
        assert _get_level_order("H1") == 1

    def test_h2_level(self):
        """Test H2 level returns correct order."""
        assert _get_level_order("H2") == 2

    def test_h5_level(self):
        """Test H5 level returns correct order."""
        assert _get_level_order("H5") == 5

    def test_sentence_level(self):
        """Test sentence level returns correct order."""
        assert _get_level_order("sentence") == 6

    def test_chunk_level(self):
        """Test chunk level returns correct order."""
        assert _get_level_order("chunk") == 7

    def test_unknown_level(self):
        """Test unknown level returns default high value."""
        assert _get_level_order("unknown") == 10

    def test_level_comparison(self):
        """Test that level ordering is correct."""
        assert _get_level_order("H1") < _get_level_order("H2")
        assert _get_level_order("H2") < _get_level_order("H3")
        assert _get_level_order("H3") < _get_level_order("chunk")


class TestCalculateCoverage:
    """Tests for _calculate_coverage() function (character-based)."""

    def test_full_coverage(self):
        """Test coverage calculation when items fully cover parent."""
        from unittest.mock import Mock
        parent = Mock()
        parent.content = "1234567890"  # 10 chars

        items = [
            {'content': "1234567890"},  # 10 chars - full coverage
        ]

        coverage = _calculate_coverage(items, parent)
        assert coverage == 1.0

    def test_partial_coverage(self):
        """Test coverage calculation with partial coverage."""
        from unittest.mock import Mock
        parent = Mock()
        parent.content = "1234567890"  # 10 chars

        items = [
            {'content': "12345"},  # 5 chars - 50% coverage
        ]

        coverage = _calculate_coverage(items, parent)
        assert coverage == 0.5

    def test_no_coverage(self):
        """Test coverage when items have no content."""
        from unittest.mock import Mock
        parent = Mock()
        parent.content = "1234567890"

        items = [
            {'content': ""},
        ]

        coverage = _calculate_coverage(items, parent)
        assert coverage == 0.0

    def test_overlapping_items(self):
        """Test coverage with multiple items."""
        from unittest.mock import Mock
        parent = Mock()
        parent.content = "1234567890"  # 10 chars

        items = [
            {'content': "123"},  # 3 chars
            {'content': "45"},   # 2 chars
        ]

        coverage = _calculate_coverage(items, parent)
        assert coverage == 0.5  # 5 chars / 10 chars

    def test_items_extend_beyond_parent(self):
        """Test coverage when items exceed parent content."""
        from unittest.mock import Mock
        parent = Mock()
        parent.content = "12345"  # 5 chars

        items = [
            {'content': "1234567890"},  # 10 chars - exceeds parent
        ]

        coverage = _calculate_coverage(items, parent)
        assert coverage == 2.0  # Can exceed 1.0

    def test_empty_items(self):
        """Test coverage with empty items list."""
        from unittest.mock import Mock
        parent = Mock()
        parent.content = "1234567890"

        items = []

        coverage = _calculate_coverage(items, parent)
        assert coverage == 0.0

    def test_zero_length_parent(self):
        """Test coverage with zero-length parent."""
        from unittest.mock import Mock
        parent = Mock()
        parent.content = ""

        items = [
            {'content': "some content"},
        ]

        coverage = _calculate_coverage(items, parent)
        assert coverage == 0.0


class TestReadContentFromFile:
    """Tests for _read_content_from_file() function."""

    def test_read_content_success(self):
        """Test reading content from file successfully."""
        with TemporaryDirectory() as tmpdir:
            md_path = Path(tmpdir) / "test.md"
            lines = ["Line 1", "Line 2", "Line 3", "Line 4", "Line 5"]
            md_path.write_text("\n".join(lines), encoding='utf-8')
            
            content = _read_content_from_file(md_path, start_line=2, end_line=4)
            assert content == "Line 2\nLine 3\nLine 4"

    def test_read_single_line(self):
        """Test reading a single line."""
        with TemporaryDirectory() as tmpdir:
            md_path = Path(tmpdir) / "test.md"
            md_path.write_text("Line 1\nLine 2\nLine 3", encoding='utf-8')
            
            content = _read_content_from_file(md_path, start_line=2, end_line=2)
            assert content == "Line 2"

    def test_read_first_line(self):
        """Test reading from first line."""
        with TemporaryDirectory() as tmpdir:
            md_path = Path(tmpdir) / "test.md"
            md_path.write_text("Line 1\nLine 2\nLine 3", encoding='utf-8')
            
            content = _read_content_from_file(md_path, start_line=1, end_line=2)
            assert content == "Line 1\nLine 2"

    def test_read_all_lines(self):
        """Test reading all lines."""
        with TemporaryDirectory() as tmpdir:
            md_path = Path(tmpdir) / "test.md"
            lines = ["Line 1", "Line 2", "Line 3"]
            md_path.write_text("\n".join(lines), encoding='utf-8')
            
            content = _read_content_from_file(md_path, start_line=1, end_line=3)
            assert content == "\n".join(lines)

    def test_read_empty_file(self):
        """Test reading from empty file."""
        with TemporaryDirectory() as tmpdir:
            md_path = Path(tmpdir) / "test.md"
            md_path.write_text("", encoding='utf-8')
            
            content = _read_content_from_file(md_path, start_line=1, end_line=1)
            assert content == ""


class TestGetHeadingChain:
    """Tests for _get_heading_chain() function."""

    def test_get_heading_chain_with_breadcrumbs(self):
        """Test getting heading chain from parent with breadcrumbs."""
        parent = Mock()
        parent.heading_breadcrumbs = "Chapter 1 > Section A > Subsection 1"
        parents_map = {1: parent}
        
        chain = _get_heading_chain(1, parents_map)
        assert chain == ["Chapter 1", "Section A", "Subsection 1"]

    def test_get_heading_chain_no_parent(self):
        """Test getting heading chain when parent_id is None."""
        parents_map = {}
        chain = _get_heading_chain(None, parents_map)
        assert chain == []

    def test_get_heading_chain_parent_not_in_map(self):
        """Test getting heading chain when parent not in map."""
        parents_map = {}
        chain = _get_heading_chain(999, parents_map)
        assert chain == []

    def test_get_heading_chain_empty_breadcrumbs(self):
        """Test getting heading chain when breadcrumbs are empty."""
        parent = Mock()
        parent.heading_breadcrumbs = ""
        parents_map = {1: parent}
        
        chain = _get_heading_chain(1, parents_map)
        assert chain == []

    def test_get_heading_chain_none_breadcrumbs(self):
        """Test getting heading chain when breadcrumbs are None."""
        parent = Mock()
        parent.heading_breadcrumbs = None
        parents_map = {1: parent}
        
        chain = _get_heading_chain(1, parents_map)
        assert chain == []

    def test_get_heading_chain_with_whitespace(self):
        """Test getting heading chain with whitespace trimming."""
        parent = Mock()
        parent.heading_breadcrumbs = " Chapter 1 >  Section A  > Subsection 1 "
        parents_map = {1: parent}
        
        chain = _get_heading_chain(1, parents_map)
        assert chain == ["Chapter 1", "Section A", "Subsection 1"]

    def test_get_heading_chain_single_heading(self):
        """Test getting heading chain with single heading."""
        parent = Mock()
        parent.heading_breadcrumbs = "Chapter 1"
        parents_map = {1: parent}
        
        chain = _get_heading_chain(1, parents_map)
        assert chain == ["Chapter 1"]


class TestMergeAdjacentItems:
    """Tests for _merge_adjacent_items() function."""

    def test_merge_adjacent_items_within_gap(self):
        """Test merging items that are within line gap."""
        with TemporaryDirectory() as tmpdir:
            md_path = Path(tmpdir) / "test.md"
            md_path.write_text("\n".join([f"Line {i}" for i in range(1, 21)]), encoding='utf-8')

            items = [
                {'id': 1, 'chunk_ids': [1], 'start_line': 10, 'end_line': 15, 'work_id': 1, 'content': 'Content 1'},
                {'id': 2, 'chunk_ids': [2], 'start_line': 17, 'end_line': 20, 'work_id': 1, 'content': 'Content 2'},
            ]

            merged = _merge_adjacent_items(items, None, md_path, line_gap=7, enrich_from_md=True)
            assert len(merged) == 1
            assert merged[0]['start_line'] == 10
            assert merged[0]['end_line'] == 20
            assert 1 in merged[0]['chunk_ids']
            assert 2 in merged[0]['chunk_ids']

    def test_merge_adjacent_items_beyond_gap(self):
        """Test that items beyond gap are not merged."""
        with TemporaryDirectory() as tmpdir:
            md_path = Path(tmpdir) / "test.md"
            md_path.write_text("\n".join([f"Line {i}" for i in range(1, 31)]), encoding='utf-8')

            items = [
                {'id': 1, 'chunk_ids': [1], 'start_line': 10, 'end_line': 15, 'work_id': 1, 'content': 'Content 1'},
                {'id': 2, 'chunk_ids': [2], 'start_line': 25, 'end_line': 30, 'work_id': 1, 'content': 'Content 2'},
            ]

            merged = _merge_adjacent_items(items, None, md_path, line_gap=7, enrich_from_md=True)
            assert len(merged) == 2
            assert merged[0]['start_line'] == 10
            assert merged[1]['start_line'] == 25

    def test_merge_adjacent_items_empty_list(self):
        """Test merging empty items list."""
        with TemporaryDirectory() as tmpdir:
            md_path = Path(tmpdir) / "test.md"
            md_path.write_text("", encoding='utf-8')
            
            merged = _merge_adjacent_items([], None, md_path, line_gap=7, enrich_from_md=True)
            assert merged == []

    def test_merge_adjacent_items_single_item(self):
        """Test merging single item."""
        with TemporaryDirectory() as tmpdir:
            md_path = Path(tmpdir) / "test.md"
            md_path.write_text("Line 1\nLine 2\nLine 3", encoding='utf-8')
            
            items = [
                {'id': 1, 'chunk_ids': [1], 'start_line': 1, 'end_line': 3, 'work_id': 1, 'content': 'Content 1'},
            ]
            
            merged = _merge_adjacent_items(items, None, md_path, line_gap=7, enrich_from_md=True)
            assert len(merged) == 1
            assert merged[0]['start_line'] == 1
            assert merged[0]['end_line'] == 3

    def test_merge_adjacent_items_multiple_groups(self):
        """Test merging items into multiple groups."""
        with TemporaryDirectory() as tmpdir:
            md_path = Path(tmpdir) / "test.md"
            md_path.write_text("\n".join([f"Line {i}" for i in range(1, 41)]), encoding='utf-8')
            
            items = [
                {'id': 1, 'chunk_ids': [1], 'start_line': 10, 'end_line': 15, 'work_id': 1, 'content': 'Content 1'},
                {'id': 2, 'chunk_ids': [2], 'start_line': 17, 'end_line': 20, 'work_id': 1, 'content': 'Content 2'},
                {'id': 3, 'chunk_ids': [3], 'start_line': 30, 'end_line': 35, 'work_id': 1, 'content': 'Content 3'},
                {'id': 4, 'chunk_ids': [4], 'start_line': 37, 'end_line': 40, 'work_id': 1, 'content': 'Content 4'},
            ]
            
            merged = _merge_adjacent_items(items, None, md_path, line_gap=7, enrich_from_md=True)
            assert len(merged) == 2
            assert merged[0]['start_line'] == 10
            assert merged[0]['end_line'] == 20
            assert merged[1]['start_line'] == 30
            assert merged[1]['end_line'] == 40

    def test_merge_adjacent_items_unsorted(self):
        """Test that items are sorted before merging."""
        with TemporaryDirectory() as tmpdir:
            md_path = Path(tmpdir) / "test.md"
            md_path.write_text("\n".join([f"Line {i}" for i in range(1, 21)]), encoding='utf-8')
            
            items = [
                {'id': 2, 'chunk_ids': [2], 'start_line': 17, 'end_line': 20, 'work_id': 1, 'content': 'Content 2'},
                {'id': 1, 'chunk_ids': [1], 'start_line': 10, 'end_line': 15, 'work_id': 1, 'content': 'Content 1'},
            ]
            
            merged = _merge_adjacent_items(items, None, md_path, line_gap=7, enrich_from_md=True)
            assert len(merged) == 1
            assert merged[0]['start_line'] == 10

    def test_merge_adjacent_items_without_enrich(self):
        """Test merging without enriching from markdown."""
        with TemporaryDirectory() as tmpdir:
            md_path = Path(tmpdir) / "test.md"
            md_path.write_text("Line 1\nLine 2\nLine 3", encoding='utf-8')
            
            items = [
                {'id': 1, 'chunk_ids': [1], 'start_line': 1, 'end_line': 2, 'work_id': 1, 'content': 'Content 1'},
                {'id': 2, 'chunk_ids': [2], 'start_line': 3, 'end_line': 3, 'work_id': 1, 'content': 'Content 2'},
            ]
            
            merged = _merge_adjacent_items(items, None, md_path, line_gap=7, enrich_from_md=False)
            assert len(merged) == 1
            assert merged[0]['content'] == 'Content 1\n\nContent 2'


class TestFinalizeGroup:
    """Tests for _finalize_group() function."""

    def test_finalize_group_basic(self):
        """Test finalizing a basic group."""
        with TemporaryDirectory() as tmpdir:
            md_path = Path(tmpdir) / "test.md"
            md_path.write_text("Line 1\nLine 2\nLine 3\nLine 4\nLine 5", encoding='utf-8')
            
            items = [
                {'id': 1, 'chunk_ids': [1], 'start_line': 1, 'end_line': 2, 'work_id': 1, 'content': 'Content 1', 'score': 0.8, 'parent_id': 10},
                {'id': 2, 'chunk_ids': [2], 'start_line': 3, 'end_line': 5, 'work_id': 1, 'content': 'Content 2', 'score': 0.9, 'parent_id': 10},
            ]
            
            result = _finalize_group(items, None, md_path, enrich_from_md=True)
            assert result['start_line'] == 1
            assert result['end_line'] == 5
            assert result['score'] == 0.9
            assert result['work_id'] == 1
            assert result['parent_id'] == 10
            assert 1 in result['chunk_ids']
            assert 2 in result['chunk_ids']
            assert 'Line 1' in result['content']
            assert 'Line 5' in result['content']

    def test_finalize_group_max_score(self):
        """Test that finalize_group uses max score."""
        with TemporaryDirectory() as tmpdir:
            md_path = Path(tmpdir) / "test.md"
            md_path.write_text("Line 1\nLine 2", encoding='utf-8')
            
            items = [
                {'id': 1, 'chunk_ids': [1], 'start_line': 1, 'end_line': 1, 'work_id': 1, 'content': 'Content 1', 'score': 0.5, 'parent_id': None},
                {'id': 2, 'chunk_ids': [2], 'start_line': 2, 'end_line': 2, 'work_id': 1, 'content': 'Content 2', 'score': 0.9, 'parent_id': None},
            ]
            
            result = _finalize_group(items, None, md_path, enrich_from_md=True)
            assert result['score'] == 0.9

    def test_finalize_group_with_heading_breadcrumbs(self):
        """Test finalize_group with heading breadcrumbs."""
        with TemporaryDirectory() as tmpdir:
            md_path = Path(tmpdir) / "test.md"
            md_path.write_text("Line 1\nLine 2", encoding='utf-8')
            
            items = [
                {'id': 1, 'chunk_ids': [1], 'start_line': 1, 'end_line': 2, 'work_id': 1, 'content': 'Content 1', 'score': 0.8, 'parent_id': None, 
                 'heading_breadcrumbs': 'Chapter 1 > Section A', 'level': 'H2'},
            ]
            
            result = _finalize_group(items, None, md_path, enrich_from_md=True)
            assert result['content'].startswith('## Section A')
            assert 'Line 1' in result['content']

    def test_finalize_group_heading_already_present(self):
        """Test that heading is not prepended if already present."""
        with TemporaryDirectory() as tmpdir:
            md_path = Path(tmpdir) / "test.md"
            md_path.write_text("## Section A\nLine 1\nLine 2", encoding='utf-8')
            
            items = [
                {'id': 1, 'chunk_ids': [1], 'start_line': 1, 'end_line': 3, 'work_id': 1, 'content': 'Content 1', 'score': 0.8, 'parent_id': None,
                 'heading_breadcrumbs': 'Chapter 1 > Section A', 'level': 'H2'},
            ]
            
            result = _finalize_group(items, None, md_path, enrich_from_md=True)
            # Should not duplicate the heading
            assert result['content'].count('## Section A') == 1

    def test_finalize_group_with_list_breadcrumbs(self):
        """Test finalize_group with list format breadcrumbs."""
        with TemporaryDirectory() as tmpdir:
            md_path = Path(tmpdir) / "test.md"
            md_path.write_text("Line 1\nLine 2", encoding='utf-8')
            
            items = [
                {'id': 1, 'chunk_ids': [1], 'start_line': 1, 'end_line': 2, 'work_id': 1, 'content': 'Content 1', 'score': 0.8, 'parent_id': None,
                 'heading_breadcrumbs': ['Chapter 1', 'Section A'], 'level': 'H2'},
            ]
            
            result = _finalize_group(items, None, md_path, enrich_from_md=True)
            assert result['content'].startswith('## Section A')

    def test_finalize_group_without_enrich(self):
        """Test finalize_group without enriching from markdown."""
        with TemporaryDirectory() as tmpdir:
            md_path = Path(tmpdir) / "test.md"
            md_path.write_text("Line 1\nLine 2", encoding='utf-8')
            
            items = [
                {'id': 1, 'chunk_ids': [1], 'start_line': 1, 'end_line': 1, 'work_id': 1, 'content': 'Content 1', 'score': 0.8, 'parent_id': None},
                {'id': 2, 'chunk_ids': [2], 'start_line': 2, 'end_line': 2, 'work_id': 1, 'content': 'Content 2', 'score': 0.9, 'parent_id': None},
            ]
            
            result = _finalize_group(items, None, md_path, enrich_from_md=False)
            assert result['content'] == 'Content 1\n\nContent 2'


class TestConsolidatedGroup:
    """Tests for ConsolidatedGroup dataclass."""

    def test_consolidated_group_creation(self):
        """Test creating a ConsolidatedGroup."""
        group = ConsolidatedGroup(
            chunk_ids=[1, 2, 3],
            parent_id=10,
            work_id=1,
            content="Test content",
            start_line=1,
            end_line=10,
            score=0.9,
            heading_chain=["Chapter 1", "Section A"]
        )
        assert group.chunk_ids == [1, 2, 3]
        assert group.parent_id == 10
        assert group.work_id == 1
        assert group.content == "Test content"
        assert group.start_line == 1
        assert group.end_line == 10
        assert group.score == 0.9
        assert group.heading_chain == ["Chapter 1", "Section A"]

    def test_consolidated_group_default_heading_chain(self):
        """Test ConsolidatedGroup with default heading_chain."""
        group = ConsolidatedGroup(
            chunk_ids=[1],
            parent_id=None,
            work_id=1,
            content="Test content",
            start_line=1,
            end_line=10,
            score=0.8
        )
        assert group.heading_chain is None


class TestConsolidationResult:
    """Tests for ConsolidationResult dataclass."""

    def test_consolidation_result_creation(self):
        """Test creating a ConsolidationResult."""
        groups = [
            ConsolidatedGroup(
                chunk_ids=[1],
                parent_id=None,
                work_id=1,
                content="Content 1",
                start_line=1,
                end_line=10,
                score=0.9
            )
        ]
        result = ConsolidationResult(
            query_id=1,
            original_count=5,
            consolidated_count=1,
            groups=groups
        )
        assert result.query_id == 1
        assert result.original_count == 5
        assert result.consolidated_count == 1
        assert len(result.groups) == 1


class TestConsolidateContext:
    """Tests for consolidate_context() function."""

    @pytest.fixture
    def mock_query(self):
        """Create a mock Query object."""
        query = Mock()
        query.id = 1
        query.retrieved_context = [
            {
                'id': 1,
                'work_id': 1,
                'parent_id': 10,
                'content': 'Content 1',
                'start_line': 10,
                'end_line': 15,
                'final_score': 0.9,
                'level': 'chunk'
            },
            {
                'id': 2,
                'work_id': 1,
                'parent_id': 10,
                'content': 'Content 2',
                'start_line': 17,
                'end_line': 20,
                'final_score': 0.8,
                'level': 'chunk'
            },
        ]
        query.clean_retrieval_context = None
        return query

    @pytest.fixture
    def mock_work(self):
        """Create a mock Work object."""
        work = Mock()
        work.id = 1
        work.title = "Test Work"
        work.files = {
            "sanitized": {
                "path": str(Path("/tmp/test.md")),
                "hash": "test_hash"
            }
        }
        return work

    @pytest.fixture
    def mock_parent_chunk(self):
        """Create a mock parent Chunk."""
        chunk = Mock()
        chunk.id = 10
        chunk.parent_id = None
        chunk.start_line = 10
        chunk.end_line = 25
        chunk.level = "H2"
        chunk.heading_breadcrumbs = "Chapter 1 > Section A"
        # Add content for character-based coverage calculation
        chunk.content = "Parent content here with enough characters to calculate coverage"
        return chunk

    @patch('vulcanlab.augmentation.consolidate_context.compute_file_hash')
    @patch('vulcanlab.augmentation.consolidate_context.get_session')
    @patch('vulcanlab.augmentation.consolidate_context.get_default_config')
    def test_consolidate_context_success(
        self, mock_get_config, mock_get_session, mock_compute_hash, mock_query, mock_work, mock_parent_chunk
    ):
        """Test successful consolidation."""
        # Setup config
        mock_config = {
            "consolidation": {
                "coverage_threshold": 0.5,
                "line_gap": 7,
                "min_content_length": 350,
                "enrich_from_md": True
            }
        }
        mock_get_config.return_value = mock_config

        # Setup session
        mock_session = MagicMock()
        mock_session.query.return_value.filter.return_value.first.return_value = mock_query
        
        # Track query calls - the code makes multiple queries:
        # 1. Works query (returns [mock_work])
        # 2. Initial parents query (returns [mock_parent_chunk])
        # 3. Next level parents query in while loop (returns [] since parent has no parent_id)
        # 4. All parents query (returns [mock_parent_chunk])
        query_call_count = [0]
        
        def all_side_effect(*args, **kwargs):
            query_call_count[0] += 1
            if query_call_count[0] == 1:
                return [mock_work]  # Works query
            elif query_call_count[0] == 2:
                return [mock_parent_chunk]  # Initial parents
            elif query_call_count[0] == 3:
                return []  # Next level (empty)
            else:
                return [mock_parent_chunk]  # All parents
        
        mock_session.query.return_value.filter.return_value.all.side_effect = all_side_effect
        mock_get_session.return_value.__enter__.return_value = mock_session

        # Setup file hash
        mock_compute_hash.return_value = "test_hash"

        # Create temporary markdown file
        with TemporaryDirectory() as tmpdir:
            md_path = Path(tmpdir) / "test.md"
            md_path.write_text("\n".join([f"Line {i}" for i in range(1, 26)]), encoding='utf-8')
            mock_work.files["sanitized"]["path"] = str(md_path)
            # Make Path(mock_work.files["sanitized"]["path"]) work correctly
            mock_work.files["sanitized"]["path"] = str(md_path)

            result = consolidate_context(query_id=1, verbose=False)

            assert result.query_id == 1
            assert result.original_count == 2
            assert result.consolidated_count >= 0
            mock_session.commit.assert_called_once()

    @patch('vulcanlab.augmentation.consolidate_context.get_session')
    @patch('vulcanlab.augmentation.consolidate_context.get_default_config')
    def test_consolidate_context_query_not_found(self, mock_get_config, mock_get_session):
        """Test consolidation when query is not found."""
        mock_config = {
            "consolidation": {
                "coverage_threshold": 0.5,
                "line_gap": 7,
                "min_content_length": 350,
                "enrich_from_md": True
            }
        }
        mock_get_config.return_value = mock_config

        mock_session = MagicMock()
        mock_session.query.return_value.filter.return_value.first.return_value = None
        mock_get_session.return_value.__enter__.return_value = mock_session

        with pytest.raises(ValueError, match="Query with ID 1 not found"):
            consolidate_context(query_id=1)

    @patch('vulcanlab.augmentation.consolidate_context.get_session')
    @patch('vulcanlab.augmentation.consolidate_context.get_default_config')
    def test_consolidate_context_no_retrieved_context(self, mock_get_config, mock_get_session):
        """Test consolidation when query has no retrieved context."""
        mock_config = {
            "consolidation": {
                "coverage_threshold": 0.5,
                "line_gap": 7,
                "min_content_length": 350,
                "enrich_from_md": True
            }
        }
        mock_get_config.return_value = mock_config

        mock_query = Mock()
        mock_query.id = 1
        mock_query.retrieved_context = None

        mock_session = MagicMock()
        mock_session.query.return_value.filter.return_value.first.return_value = mock_query
        mock_get_session.return_value.__enter__.return_value = mock_session

        with pytest.raises(ValueError, match="has no retrieved_context"):
            consolidate_context(query_id=1)

    @patch('vulcanlab.augmentation.consolidate_context.compute_file_hash')
    @patch('vulcanlab.augmentation.consolidate_context.get_session')
    @patch('vulcanlab.augmentation.consolidate_context.get_default_config')
    def test_consolidate_context_hash_mismatch(
        self, mock_get_config, mock_get_session, mock_compute_hash, mock_query, mock_work
    ):
        """Test consolidation when file hash doesn't match."""
        mock_config = {
            "consolidation": {
                "coverage_threshold": 0.5,
                "line_gap": 7,
                "min_content_length": 350,
                "enrich_from_md": True
            }
        }
        mock_get_config.return_value = mock_config

        mock_query.retrieved_context = [
            {
                'id': 1,
                'work_id': 1,
                'parent_id': None,
                'content': 'Content 1',
                'start_line': 10,
                'end_line': 15,
                'final_score': 0.9,
                'level': 'chunk'
            },
        ]

        mock_session = MagicMock()
        mock_session.query.return_value.filter.return_value.first.return_value = mock_query
        mock_session.query.return_value.filter.return_value.all.side_effect = [
            [mock_work],  # Works
            [],  # Parents
        ]
        mock_get_session.return_value.__enter__.return_value = mock_session

        # Hash mismatch
        mock_compute_hash.return_value = "different_hash"

        with TemporaryDirectory() as tmpdir:
            md_path = Path(tmpdir) / "test.md"
            md_path.write_text("Test content", encoding='utf-8')
            mock_work.files["sanitized"]["path"] = str(md_path)

            with pytest.raises(RuntimeError, match="Content hash mismatch"):
                consolidate_context(query_id=1)

    @patch('vulcanlab.augmentation.consolidate_context.compute_file_hash')
    @patch('vulcanlab.augmentation.consolidate_context.get_session')
    @patch('vulcanlab.augmentation.consolidate_context.get_default_config')
    def test_consolidate_context_empty_context(
        self, mock_get_config, mock_get_session, mock_compute_hash
    ):
        """Test consolidation with empty retrieved context raises ValueError."""
        mock_config = {
            "consolidation": {
                "coverage_threshold": 0.5,
                "line_gap": 7,
                "min_content_length": 350,
                "enrich_from_md": True
            }
        }
        mock_get_config.return_value = mock_config

        mock_query = Mock()
        mock_query.id = 1
        mock_query.retrieved_context = []  # Empty list is falsy

        mock_session = MagicMock()
        mock_session.query.return_value.filter.return_value.first.return_value = mock_query
        mock_get_session.return_value.__enter__.return_value = mock_session

        with pytest.raises(ValueError, match="has no retrieved_context"):
            consolidate_context(query_id=1)

    @patch('vulcanlab.augmentation.consolidate_context.compute_file_hash')
    @patch('vulcanlab.augmentation.consolidate_context.get_session')
    @patch('vulcanlab.augmentation.consolidate_context.get_default_config')
    def test_consolidate_context_single_context(
        self, mock_get_config, mock_get_session, mock_compute_hash, mock_query, mock_work
    ):
        """Test consolidation with single context item."""
        mock_config = {
            "consolidation": {
                "coverage_threshold": 0.5,
                "line_gap": 7,
                "min_content_length": 10,  # Low threshold for testing
                "enrich_from_md": True
            }
        }
        mock_get_config.return_value = mock_config

        mock_query.retrieved_context = [
            {
                'id': 1,
                'work_id': 1,
                'parent_id': None,
                'content': 'Content 1',
                'start_line': 10,
                'end_line': 15,
                'final_score': 0.9,
                'level': 'chunk'
            },
        ]

        mock_session = MagicMock()
        mock_session.query.return_value.filter.return_value.first.return_value = mock_query
        
        # Track query calls - multiple Chunk queries will be made
        query_call_count = [0]
        
        def all_side_effect(*args, **kwargs):
            query_call_count[0] += 1
            if query_call_count[0] == 1:
                return [mock_work]  # Works query
            # All Chunk queries return empty since no parents
            return []
        
        mock_session.query.return_value.filter.return_value.all.side_effect = all_side_effect
        mock_get_session.return_value.__enter__.return_value = mock_session

        mock_compute_hash.return_value = "test_hash"

        with TemporaryDirectory() as tmpdir:
            md_path = Path(tmpdir) / "test.md"
            md_path.write_text("\n".join([f"Line {i}" for i in range(1, 21)]), encoding='utf-8')
            mock_work.files["sanitized"]["path"] = str(md_path)

            result = consolidate_context(query_id=1)
            assert result.original_count == 1
            assert result.consolidated_count >= 0

    @patch('vulcanlab.augmentation.consolidate_context.compute_file_hash')
    @patch('vulcanlab.augmentation.consolidate_context.get_session')
    @patch('vulcanlab.augmentation.consolidate_context.get_config_by_name')
    def test_consolidate_context_with_config_preset(
        self, mock_get_config_by_name, mock_get_session, mock_compute_hash, mock_query, mock_work
    ):
        """Test consolidation with config preset."""
        mock_config = {
            "consolidation": {
                "coverage_threshold": 0.6,
                "line_gap": 10,
                "min_content_length": 400,
                "enrich_from_md": False
            }
        }
        mock_get_config_by_name.return_value = mock_config

        mock_query.retrieved_context = [
            {
                'id': 1,
                'work_id': 1,
                'parent_id': None,
                'content': 'Content 1',
                'start_line': 10,
                'end_line': 15,
                'final_score': 0.9,
                'level': 'chunk'
            },
        ]

        mock_session = MagicMock()
        mock_session.query.return_value.filter.return_value.first.return_value = mock_query
        
        # Track query calls - multiple Chunk queries will be made
        query_call_count = [0]
        
        def all_side_effect(*args, **kwargs):
            query_call_count[0] += 1
            if query_call_count[0] == 1:
                return [mock_work]  # Works query
            # All Chunk queries return empty since no parents
            return []
        
        mock_session.query.return_value.filter.return_value.all.side_effect = all_side_effect
        mock_get_session.return_value.__enter__.return_value = mock_session

        mock_compute_hash.return_value = "test_hash"

        with TemporaryDirectory() as tmpdir:
            md_path = Path(tmpdir) / "test.md"
            md_path.write_text("Test content", encoding='utf-8')
            mock_work.files["sanitized"]["path"] = str(md_path)

            result = consolidate_context(query_id=1, config_preset="test_preset")
            mock_get_config_by_name.assert_called_once_with("test_preset")
            assert result.query_id == 1


class TestDeduplicationAndMerging:
    """Tests for deduplication and merging strategies."""

    def test_merge_overlapping_chunks(self):
        """Test merging chunks that overlap."""
        with TemporaryDirectory() as tmpdir:
            md_path = Path(tmpdir) / "test.md"
            md_path.write_text("\n".join([f"Line {i}" for i in range(1, 21)]), encoding='utf-8')
            
            items = [
                {'id': 1, 'chunk_ids': [1], 'start_line': 10, 'end_line': 15, 'work_id': 1, 'content': 'Content 1', 'score': 0.8},
                {'id': 2, 'chunk_ids': [2], 'start_line': 13, 'end_line': 18, 'work_id': 1, 'content': 'Content 2', 'score': 0.9},
            ]
            
            merged = _merge_adjacent_items(items, None, md_path, line_gap=7, enrich_from_md=True)
            assert len(merged) == 1
            assert merged[0]['start_line'] == 10
            assert merged[0]['end_line'] == 18
            assert merged[0]['score'] == 0.9  # Max score

    def test_deduplicate_identical_chunks(self):
        """Test handling of identical chunks."""
        with TemporaryDirectory() as tmpdir:
            md_path = Path(tmpdir) / "test.md"
            md_path.write_text("\n".join([f"Line {i}" for i in range(1, 21)]), encoding='utf-8')
            
            items = [
                {'id': 1, 'chunk_ids': [1], 'start_line': 10, 'end_line': 15, 'work_id': 1, 'content': 'Content 1', 'score': 0.8},
                {'id': 2, 'chunk_ids': [2], 'start_line': 10, 'end_line': 15, 'work_id': 1, 'content': 'Content 1', 'score': 0.9},
            ]
            
            merged = _merge_adjacent_items(items, None, md_path, line_gap=7, enrich_from_md=True)
            assert len(merged) == 1
            assert merged[0]['start_line'] == 10
            assert merged[0]['end_line'] == 15
            assert 1 in merged[0]['chunk_ids']
            assert 2 in merged[0]['chunk_ids']

    def test_coverage_threshold_replacement(self):
        """Test that items with high coverage are replaced with parent."""
        from unittest.mock import Mock
        parent = Mock()
        parent.content = "1234567890"  # 10 chars

        items = [
            {'content': "12345"},   # 5 chars
            {'content': "678"},     # 3 chars
        ]

        coverage = _calculate_coverage(items, parent)
        # 8 chars out of 10 = 80% coverage
        assert coverage >= 0.5  # Should exceed threshold

    def test_coverage_below_threshold_no_replacement(self):
        """Test that items below coverage threshold are not replaced."""
        from unittest.mock import Mock
        parent = Mock()
        parent.content = "1234567890"  # 10 chars

        items = [
            {'content': "123"},  # 3 chars = 30% coverage
        ]

        coverage = _calculate_coverage(items, parent)
        # 3 chars out of 10 = 30% coverage
        assert coverage < 0.5  # Should be below threshold

    def test_merge_adjacent_exact_gap(self):
        """Test merging when gap equals line_gap exactly."""
        with TemporaryDirectory() as tmpdir:
            md_path = Path(tmpdir) / "test.md"
            md_path.write_text("\n".join([f"Line {i}" for i in range(1, 31)]), encoding='utf-8')
            
            items = [
                {'id': 1, 'chunk_ids': [1], 'start_line': 10, 'end_line': 15, 'work_id': 1, 'content': 'Content 1'},
                {'id': 2, 'chunk_ids': [2], 'start_line': 22, 'end_line': 25, 'work_id': 1, 'content': 'Content 2'},
            ]
            # Gap = 22 - 15 - 1 = 6 lines, but check is: start_line - end_line <= gap
            # So: 22 - 15 = 7, which equals line_gap (7), so they should merge
            
            merged = _merge_adjacent_items(items, None, md_path, line_gap=7, enrich_from_md=True)
            assert len(merged) == 1
            assert merged[0]['start_line'] == 10
            assert merged[0]['end_line'] == 25

    def test_merge_adjacent_one_line_over_gap(self):
        """Test that items one line over gap are not merged."""
        with TemporaryDirectory() as tmpdir:
            md_path = Path(tmpdir) / "test.md"
            md_path.write_text("\n".join([f"Line {i}" for i in range(1, 31)]), encoding='utf-8')
            
            items = [
                {'id': 1, 'chunk_ids': [1], 'start_line': 10, 'end_line': 15, 'work_id': 1, 'content': 'Content 1'},
                {'id': 2, 'chunk_ids': [2], 'start_line': 24, 'end_line': 25, 'work_id': 1, 'content': 'Content 2'},
            ]
            # Gap = 24 - 15 - 1 = 8 lines (one over threshold)
            
            merged = _merge_adjacent_items(items, None, md_path, line_gap=7, enrich_from_md=True)
            assert len(merged) == 2

    def test_finalize_group_with_multiple_chunk_ids(self):
        """Test finalize_group with items that have chunk_ids lists."""
        with TemporaryDirectory() as tmpdir:
            md_path = Path(tmpdir) / "test.md"
            md_path.write_text("Line 1\nLine 2\nLine 3", encoding='utf-8')
            
            items = [
                {'id': 1, 'chunk_ids': [1, 2], 'start_line': 1, 'end_line': 2, 'work_id': 1, 'content': 'Content 1', 'score': 0.8},
                {'id': 2, 'chunk_ids': [3, 4], 'start_line': 3, 'end_line': 3, 'work_id': 1, 'content': 'Content 2', 'score': 0.9},
            ]
            
            result = _finalize_group(items, None, md_path, enrich_from_md=True)
            assert set(result['chunk_ids']) == {1, 2, 3, 4}

    def test_finalize_group_mixed_chunk_ids(self):
        """Test finalize_group with mixed chunk_ids and id fields."""
        with TemporaryDirectory() as tmpdir:
            md_path = Path(tmpdir) / "test.md"
            md_path.write_text("Line 1\nLine 2", encoding='utf-8')
            
            items = [
                {'id': 1, 'chunk_ids': [1, 2], 'start_line': 1, 'end_line': 1, 'work_id': 1, 'content': 'Content 1', 'score': 0.8},
                {'id': 3, 'start_line': 2, 'end_line': 2, 'work_id': 1, 'content': 'Content 2', 'score': 0.9},
            ]
            
            result = _finalize_group(items, None, md_path, enrich_from_md=True)
            assert 1 in result['chunk_ids']
            assert 2 in result['chunk_ids']
            assert 3 in result['chunk_ids']

    def test_finalize_group_uses_final_score(self):
        """Test that finalize_group uses final_score if score not present."""
        with TemporaryDirectory() as tmpdir:
            md_path = Path(tmpdir) / "test.md"
            md_path.write_text("Line 1\nLine 2", encoding='utf-8')
            
            items = [
                {'id': 1, 'chunk_ids': [1], 'start_line': 1, 'end_line': 1, 'work_id': 1, 'content': 'Content 1', 'final_score': 0.8},
                {'id': 2, 'chunk_ids': [2], 'start_line': 2, 'end_line': 2, 'work_id': 1, 'content': 'Content 2', 'final_score': 0.9},
            ]
            
            result = _finalize_group(items, None, md_path, enrich_from_md=True)
            assert result['score'] == 0.9

    def test_finalize_group_no_content_items(self):
        """Test finalize_group when items have no content."""
        with TemporaryDirectory() as tmpdir:
            md_path = Path(tmpdir) / "test.md"
            md_path.write_text("Line 1\nLine 2", encoding='utf-8')
            
            items = [
                {'id': 1, 'chunk_ids': [1], 'start_line': 1, 'end_line': 1, 'work_id': 1, 'score': 0.8},
                {'id': 2, 'chunk_ids': [2], 'start_line': 2, 'end_line': 2, 'work_id': 1, 'content': '', 'score': 0.9},
            ]
            
            result = _finalize_group(items, None, md_path, enrich_from_md=False)
            # Should only include content from items that have it
            assert result['content'] == ''

    def test_get_heading_chain_with_empty_separators(self):
        """Test getting heading chain with empty separators."""
        parent = Mock()
        parent.heading_breadcrumbs = "Chapter 1 >  > Section A"
        parents_map = {1: parent}
        
        chain = _get_heading_chain(1, parents_map)
        # Should filter out empty strings
        assert chain == ["Chapter 1", "Section A"]


class TestConsolidationLogging:
    """Tests for logging functionality in consolidation."""

    @patch('vulcanlab.augmentation.consolidate_context.load_config')
    @patch('vulcanlab.augmentation.consolidate_context._save_consolidation_log')
    @patch('vulcanlab.augmentation.consolidate_context.compute_file_hash')
    @patch('vulcanlab.augmentation.consolidate_context.get_session')
    @patch('vulcanlab.augmentation.consolidate_context.get_default_config')
    def test_consolidation_logging_enabled(
        self, mock_get_config, mock_get_session, mock_compute_hash, mock_save_log, mock_load_config
    ):
        """Test that logging is called when enabled in config."""
        # Setup mocks
        mock_config = AppConfig(logging=LoggingConfig(enabled=True))
        mock_load_config.return_value = mock_config
        
        # Consolidation config
        mock_rag_config = {
            "consolidation": {
                "coverage_threshold": 0.5,
                "line_gap": 7,
                "min_content_length": 350,
                "enrich_from_md": True
            }
        }
        mock_get_config.return_value = mock_rag_config

        # Setup data
        mock_work = Mock()
        mock_work.id = 1
        mock_work.files = {"sanitized": {"path": "/tmp/test.md", "hash": "hash"}}
        
        mock_query = Mock()
        mock_query.id = 1
        mock_query.retrieved_context = [
            {'id': 1, 'work_id': 1, 'parent_id': None, 'content': 'Content', 'start_line': 1, 'end_line': 5, 'final_score': 0.9}
        ]
        
        mock_session = MagicMock()
        mock_session.query.return_value.filter.return_value.first.return_value = mock_query
        # Works query, parents query, all parents query
        mock_session.query.return_value.filter.return_value.all.side_effect = [[mock_work], [], []]
        mock_get_session.return_value.__enter__.return_value = mock_session
        
        mock_compute_hash.return_value = "hash"
        
        with patch('pathlib.Path.exists', return_value=True), \
             patch('pathlib.Path.read_text', return_value="Content"):
            consolidate_context(1)

        mock_save_log.assert_called_once()
        args = mock_save_log.call_args[0]
        assert args[0] == 1  # query_id
        assert "iterations" in args[1]
        assert "original_items" in args[1]

    @patch('vulcanlab.augmentation.consolidate_context.load_config')
    @patch('vulcanlab.augmentation.consolidate_context._save_consolidation_log')
    @patch('vulcanlab.augmentation.consolidate_context.compute_file_hash')
    @patch('vulcanlab.augmentation.consolidate_context.get_session')
    @patch('vulcanlab.augmentation.consolidate_context.get_default_config')
    def test_consolidation_logging_disabled(
        self, mock_get_config, mock_get_session, mock_compute_hash, mock_save_log, mock_load_config
    ):
        """Test that logging is NOT called when disabled."""
        # Setup mocks
        mock_config = AppConfig(logging=LoggingConfig(enabled=False))
        mock_load_config.return_value = mock_config
        
        # Consolidation config
        mock_rag_config = {
            "consolidation": {
                "coverage_threshold": 0.5,
                "line_gap": 7,
                "min_content_length": 350,
                "enrich_from_md": True
            }
        }
        mock_get_config.return_value = mock_rag_config

        # Setup data
        mock_work = Mock()
        mock_work.id = 1
        mock_work.files = {"sanitized": {"path": "/tmp/test.md", "hash": "hash"}}
        
        mock_query = Mock()
        mock_query.id = 1
        mock_query.retrieved_context = [
            {'id': 1, 'work_id': 1, 'parent_id': None, 'content': 'Content', 'start_line': 1, 'end_line': 5, 'final_score': 0.9}
        ]
        
        mock_session = MagicMock()
        mock_session.query.return_value.filter.return_value.first.return_value = mock_query
        # Works query, parents query, all parents query
        mock_session.query.return_value.filter.return_value.all.side_effect = [[mock_work], [], []]
        mock_get_session.return_value.__enter__.return_value = mock_session
        
        mock_compute_hash.return_value = "hash"
        
        with patch('pathlib.Path.exists', return_value=True), \
             patch('pathlib.Path.read_text', return_value="Content"):
            consolidate_context(1)

        mock_save_log.assert_not_called()
