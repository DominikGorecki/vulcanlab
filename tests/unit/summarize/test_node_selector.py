import pytest
from unittest.mock import MagicMock, patch
from sqlalchemy import select

from vulcanlab.data.models.chunk import Chunk
from vulcanlab.data.models.sanitized_markdown import SanitizedMarkdown
from vulcanlab.summarize.node_selector import (
    SelectedNode,
    load_heading_chunks,
    build_chunk_tree,
    detect_content_gaps,
    compute_effective_boundaries,
    get_content_for_node,
    select_nodes_for_summarization
)
from vulcanlab.summarize.salience import SalienceWeights


@pytest.fixture
def mock_session():
    return MagicMock()


@pytest.fixture
def sample_chunks():
    # H1 at line 1
    # H2 at line 10
    # H3 at line 20
    c1 = Chunk(id=1, level="H1", work_id=1, start_line=1, end_line=100, content="# H1", parent_id=None)
    c2 = Chunk(id=2, level="H2", work_id=1, start_line=10, end_line=50, content="## H2", parent_id=1)
    c3 = Chunk(id=3, level="H3", work_id=1, start_line=20, end_line=30, content="### H3", parent_id=2)
    c4 = Chunk(id=4, level="H1-chunk", work_id=1, start_line=2, end_line=9, content="Content", parent_id=1)
    return [c1, c2, c3, c4]


def test_load_heading_chunks(mock_session, sample_chunks):
    # Mock session.execute().scalars().all()
    mock_result = MagicMock()
    # Filter out H1-chunk
    heading_chunks = [c for c in sample_chunks if c.level in ["H1", "H2", "H3", "H4", "H5"]]
    mock_result.scalars.return_value.all.return_value = heading_chunks
    mock_session.execute.return_value = mock_result
    
    result = load_heading_chunks(work_id=1, session=mock_session)
    
    assert len(result) == 3
    assert all(c.level in ["H1", "H2", "H3", "H4", "H5"] for c in result)
    # Check that it uses the correct query
    args, _ = mock_session.execute.call_args
    assert isinstance(args[0], type(select(Chunk)))


def test_build_chunk_tree(sample_chunks):
    heading_chunks = [c for c in sample_chunks if c.level in ["H1", "H2", "H3", "H4", "H5"]]
    tree = build_chunk_tree(heading_chunks)
    
    assert 1 in tree
    assert 2 in tree
    assert tree[1] == [heading_chunks[1]] # H2 is child of H1
    assert tree[2] == [heading_chunks[2]] # H3 is child of H2


def test_detect_content_gaps(sample_chunks):
    heading_chunks = [c for c in sample_chunks if c.level in ["H1", "H2", "H3", "H4", "H5"]]
    tree = build_chunk_tree(heading_chunks)
    gaps = detect_content_gaps(heading_chunks, tree)
    
    # H1 is at line 1, first child H2 is at line 10. Gap is 2-9.
    assert 1 in gaps
    assert gaps[1] == (2, 9)
    
    # H2 is at line 10, first child H3 is at line 20. Gap is 11-19.
    assert 2 in gaps
    assert gaps[2] == (11, 19)
    
    # H3 has no children, no gap (detect_content_gaps only looks for gaps before children)
    assert 3 not in gaps


def test_compute_effective_boundaries(sample_chunks):
    c1 = sample_chunks[0] # H1, line 1-100
    c2 = sample_chunks[1] # H2, line 10-50
    
    # With children
    start, end = compute_effective_boundaries(c1, [c2])
    assert start == 1
    assert end == 9
    
    # Without children
    start, end = compute_effective_boundaries(c2, [])
    assert start == 10
    assert end == 50


def test_get_content_for_node():
    lines = ["Line 1", "Line 2", "Line 3", "Line 4", "Line 5"]
    
    # Single line
    assert get_content_for_node(lines, 1, 1) == "Line 1"
    
    # Range
    assert get_content_for_node(lines, 2, 4) == "Line 2\nLine 3\nLine 4"
    
    # Out of bounds
    assert get_content_for_node(lines, 10, 12) == ""
    
    # Empty lines
    assert get_content_for_node([], 1, 1) == ""


@patch("vulcanlab.summarize.node_selector.load_salience_weights")
@patch("vulcanlab.summarize.node_selector.compute_salience_score")
def test_select_nodes_for_summarization(mock_score, mock_weights, mock_session, sample_chunks):
    # Setup mocks
    mock_weights.return_value = SalienceWeights(
        h1_always_summarize=True,
        h2_top_percent=100,
        h3_salience_threshold=0.5,
        h4_salience_threshold=0.7,
        definition_density_weight=0.2,
        list_density_weight=0.2,
        keyphrase_novelty_weight=0.2,
        location_prior_weight=0.2,
        heading_depth_weight=0.2
    )
    
    # Scores: H1=1.0, H2=0.8, H3=0.1 (H3 should be filtered out)
    mock_score.side_effect = [1.0, 0.8, 0.1]
    
    # Mock load_heading_chunks result
    heading_chunks = [c for c in sample_chunks if c.level in ["H1", "H2", "H3", "H4", "H5"]]
    mock_exec_chunks = MagicMock()
    mock_exec_chunks.scalars.return_value.all.return_value = heading_chunks
    
    # Mock SanitizedMarkdown result
    mock_sanitized = MagicMock(spec=SanitizedMarkdown)
    mock_sanitized.content = "\n".join([f"Line {i}" for i in range(1, 101)])
    mock_exec_sanitized = MagicMock()
    mock_exec_sanitized.scalar_one_or_none.return_value = mock_sanitized
    
    # Mock session.execute to return different things for different queries
    # We can use side_effect to return different values
    mock_session.execute.side_effect = [mock_exec_chunks, mock_exec_sanitized]
    
    nodes = select_nodes_for_summarization(work_id=1, session=mock_session)
    
    # Expected nodes:
    # 1. H1 heading (Line 1)
    # 2. H1 content gap (Lines 2-9)
    # 3. H2 heading (Line 10)
    # 4. H2 content gap (Lines 11-19)
    # H3 is skipped because score 0.1 < 0.5
    
    assert len(nodes) == 4
    
    assert nodes[0].level == "H1"
    assert nodes[0].start_line == 1
    
    assert nodes[1].level == "H1-content"
    assert nodes[1].start_line == 2
    assert nodes[1].end_line == 9
    
    assert nodes[2].level == "H2"
    assert nodes[2].start_line == 10
    
    assert nodes[3].level == "H2-content"
    assert nodes[3].start_line == 11
    assert nodes[3].end_line == 19


def test_empty_work(mock_session):
    mock_result = MagicMock()
    mock_result.scalars.return_value.all.return_value = []
    mock_session.execute.return_value = mock_result
    
    nodes = select_nodes_for_summarization(work_id=1, session=mock_session)
    assert nodes == []
