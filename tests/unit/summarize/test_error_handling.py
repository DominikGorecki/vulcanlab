import pytest
from unittest.mock import MagicMock, patch
from vulcanlab.summarize.orchestrator import summarize_work, SummarizationStatus
from vulcanlab.summarize.exceptions import SummarizationError, InsufficientEvidenceError
from vulcanlab.summarize.node_selector import SelectedNode

@pytest.fixture
def mock_nodes():
    return [
        SelectedNode(chunk_id=1, content="content1", heading_path="path1", level=1, start_line=1, end_line=10, salience_score=0.5, has_content_gap=False),
        SelectedNode(chunk_id=2, content="content2", heading_path="path2", level=1, start_line=11, end_line=20, salience_score=0.5, has_content_gap=False),
        SelectedNode(chunk_id=3, content="content3", heading_path="path3", level=1, start_line=21, end_line=30, salience_score=0.5, has_content_gap=False),
    ]

@patch("vulcanlab.summarize.orchestrator.select_nodes_for_summarization")
@patch("vulcanlab.summarize.orchestrator.load_full_content")
@patch("vulcanlab.summarize.orchestrator.process_single_node")
@patch("vulcanlab.summarize.orchestrator.get_summarization_status")
def test_node_error_isolation(mock_status, mock_process, mock_load, mock_select, mock_nodes):
    # Setup: node2 fails with SummarizationError
    mock_select.return_value = mock_nodes
    mock_load.return_value = "full content"
    mock_status.return_value = None
    
    mock_session = MagicMock()
    
    # Mock responses: success, failure, success
    mock_process.side_effect = [
        (MagicMock(), MagicMock(token_usage=None)),
        SummarizationError("node2 failed", chunk_id=2),
        (MagicMock(), MagicMock(token_usage=None))
    ]
    
    progress = summarize_work(1, mock_session)
    
    # Assertions
    assert progress.status == SummarizationStatus.COMPLETED
    assert progress.completed_nodes == 2
    assert len(progress.failed_nodes) == 1
    assert progress.failed_nodes[0]["chunk_id"] == 2
    assert "node2 failed" in progress.failed_nodes[0]["error"]

@patch("vulcanlab.summarize.orchestrator.select_nodes_for_summarization")
@patch("vulcanlab.summarize.orchestrator.load_full_content")
@patch("vulcanlab.summarize.orchestrator.process_single_node")
@patch("vulcanlab.summarize.orchestrator.get_summarization_status")
def test_unrecoverable_error_stops_processing(mock_status, mock_process, mock_load, mock_select, mock_nodes):
    # Setup: node1 fails with unexpected Exception (e.g. DB error)
    mock_select.return_value = mock_nodes
    mock_load.return_value = "full content"
    mock_status.return_value = None
    
    mock_session = MagicMock()
    mock_process.side_effect = Exception("DB error")
    
    with pytest.raises(Exception) as excinfo:
        summarize_work(1, mock_session)
    
    assert "DB error" in str(excinfo.value)
    
    # Check progress cache (it should be FAILED)
    from vulcanlab.summarize.orchestrator import _progress_cache
    progress = _progress_cache[1]
    assert progress.status == SummarizationStatus.FAILED
    assert progress.error == "DB error"

@patch("vulcanlab.summarize.orchestrator.select_nodes_for_summarization")
@patch("vulcanlab.summarize.orchestrator.load_full_content")
@patch("vulcanlab.summarize.orchestrator.process_single_node")
def test_resume_skips_completed_nodes(mock_process, mock_load, mock_select, mock_nodes):
    mock_select.return_value = mock_nodes
    mock_load.return_value = "full content"
    mock_session = MagicMock()
    
    # Mock database call that finds completed chunk IDs
    # Instead of mocking select(), we mock the session.execute() result
    mock_session.execute.return_value.scalars.return_value.all.return_value = [1]
    
    from vulcanlab.summarize.orchestrator import resume_summarization
    
    mock_process.return_value = (MagicMock(), MagicMock(token_usage=None))
    
    # We need to make sure select() in resume_summarization works with our mocks
    # Actually, the error was because I mocked SummaryNode itself, which SQLAlchemy select() uses.
    # By removing @patch("vulcanlab.summarize.orchestrator.SummaryNode"), it should work.
    
    progress = resume_summarization(1, mock_session)
    
    assert progress.completed_nodes == 3 # 1 (already done) + 2 (processed now)
    assert mock_process.call_count == 2
    # Check that it called process_single_node for node2 and node3, not node1
    args_list = mock_process.call_args_list
    assert args_list[0][0][1].chunk_id == 2
    assert args_list[1][0][1].chunk_id == 3
