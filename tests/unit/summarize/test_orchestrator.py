import pytest
from unittest.mock import MagicMock, patch, call
from sqlalchemy import select

from vulcanlab.summarize.orchestrator import (
    SummarizationStatus,
    SummarizationProgress,
    get_summarization_status,
    delete_existing_summaries,
    create_summary_node,
    process_single_node,
    summarize_work,
    resume_summarization,
    _progress_cache
)
from vulcanlab.summarize.node_selector import SelectedNode
from vulcanlab.summarize.llm_summarize import SummaryResponse, KeyPoint
from vulcanlab.data.models.summary_node import SummaryNode
from vulcanlab.data.models.work_summary import WorkSummary


@pytest.fixture(autouse=True)
def clear_cache():
    _progress_cache.clear()


@pytest.fixture
def mock_session():
    return MagicMock()


def test_get_summarization_status_empty(mock_session):
    mock_result = MagicMock()
    mock_result.scalar.return_value = 0
    mock_session.execute.return_value = mock_result
    
    status = get_summarization_status(1, mock_session)
    assert status is None


def test_get_summarization_status_completed(mock_session):
    mock_result = MagicMock()
    mock_result.scalar.return_value = 5
    mock_session.execute.return_value = mock_result
    
    status = get_summarization_status(1, mock_session)
    assert status.status == SummarizationStatus.COMPLETED
    assert status.total_nodes == 5


def test_delete_existing_summaries(mock_session):
    _progress_cache[1] = SummarizationProgress(1, SummarizationStatus.COMPLETED, 5, 5)
    
    delete_existing_summaries(1, mock_session)
    
    assert 1 not in _progress_cache
    assert mock_session.commit.called
    # Should call delete for SummaryNode and WorkSummary
    assert mock_session.execute.call_count == 2


def test_create_summary_node(mock_session):
    selected = SelectedNode(
        chunk_id=10, level="H1", content="Text", heading_path="H1",
        start_line=1, end_line=1, salience_score=1.0, has_content_gap=False
    )
    response = SummaryResponse(
        gist="Gist", 
        key_points=[KeyPoint(text="P1", start_line=1, end_line=1)]
    )
    
    node = create_summary_node(1, selected, response, mock_session)
    
    assert node.work_id == 1
    assert node.gist == "Gist"
    assert node.key_points == [{"text": "P1", "start_line": 1, "end_line": 1}]
    assert mock_session.add.called
    assert mock_session.commit.called


@patch("vulcanlab.summarize.orchestrator.segment_sentences_with_lines")
@patch("vulcanlab.summarize.orchestrator.build_evidence_packet")
@patch("vulcanlab.summarize.orchestrator.summarize_node")
@patch("vulcanlab.summarize.orchestrator.create_summary_node")
def test_process_single_node(mock_create, mock_summarize, mock_evidence, mock_segment, mock_session):
    selected = SelectedNode(
        chunk_id=10, level="H1", content="Text", heading_path="H1",
        start_line=1, end_line=1, salience_score=1.0, has_content_gap=False
    )
    
    process_single_node(1, selected, "Full content", mock_session)
    
    assert mock_segment.called
    assert mock_evidence.called
    assert mock_summarize.called
    assert mock_create.called


@patch("vulcanlab.summarize.orchestrator.select_nodes_for_summarization")
@patch("vulcanlab.summarize.orchestrator.load_full_content")
@patch("vulcanlab.summarize.orchestrator.process_single_node")
def test_summarize_work(mock_process, mock_load, mock_select, mock_session):
    # Mock get_summarization_status to return None (never started)
    mock_result = MagicMock()
    mock_result.scalar.return_value = 0
    mock_session.execute.return_value = mock_result
    
    mock_select.return_value = [
        SelectedNode(10, "H1", "T1", "P1", 1, 1, 1.0, False),
        SelectedNode(11, "H2", "T2", "P2", 2, 2, 1.0, False)
    ]
    mock_load.return_value = "Full"
    
    progress = summarize_work(1, mock_session)
    
    assert progress.status == SummarizationStatus.COMPLETED
    assert progress.total_nodes == 2
    assert progress.completed_nodes == 2
    assert mock_process.call_count == 2


@patch("vulcanlab.summarize.orchestrator.select_nodes_for_summarization")
@patch("vulcanlab.summarize.orchestrator.load_full_content")
@patch("vulcanlab.summarize.orchestrator.process_single_node")
def test_resume_summarization(mock_process, mock_load, mock_select, mock_session):
    # 2 nodes total
    n1 = SelectedNode(10, "H1", "T1", "P1", 1, 1, 1.0, False)
    n2 = SelectedNode(11, "H2", "T2", "P2", 2, 2, 1.0, False)
    mock_select.return_value = [n1, n2]
    
    # Node 10 is already done
    mock_result = MagicMock()
    mock_result.scalars.return_value.all.return_value = [10]
    mock_session.execute.return_value = mock_result
    
    progress = resume_summarization(1, mock_session)
    
    assert progress.completed_nodes == 2 # 1 already done + 1 processed now
    assert progress.total_nodes == 2
    assert mock_process.call_count == 1
    # Check that only node 11 was processed
    mock_process.assert_called_once_with(1, n2, mock_load.return_value, mock_session)
