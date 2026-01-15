import pytest
import time
from unittest.mock import MagicMock, patch
from vulcanlab.summarize.orchestrator import summarize_work, resume_summarization, SummarizationStatus
from vulcanlab.summarize.llm_summarize import TokenUsage, SummaryResponse, summarize_node
from vulcanlab.summarize.evidence import EvidencePacket

@pytest.fixture
def db_session():
    return MagicMock()

@patch("vulcanlab.summarize.orchestrator.logger")
@patch("vulcanlab.summarize.orchestrator.select_nodes_for_summarization")
@patch("vulcanlab.summarize.orchestrator.load_full_content")
@patch("vulcanlab.summarize.orchestrator.process_single_node")
@patch("vulcanlab.summarize.orchestrator.get_summarization_status")
def test_summarize_work_logging_and_tokens(
    mock_status, mock_process, mock_load, mock_select, mock_logger, db_session
):
    # Setup
    work_id = 123
    mock_status.return_value = None
    
    mock_node = MagicMock()
    mock_node.chunk_id = "chunk_1"
    mock_node.level = "H1"
    mock_node.heading_path = "Introduction"
    mock_select.return_value = [mock_node]
    mock_load.return_value = "Full content"
    
    summary_node = MagicMock()
    summary_resp = SummaryResponse(
        gist="Test gist",
        token_usage=TokenUsage(input_tokens=10, output_tokens=20, model="test-model")
    )
    mock_process.return_value = (summary_node, summary_resp)
    
    # Run
    progress = summarize_work(work_id, db_session)
    
    # Verify progress object
    assert progress.total_input_tokens == 10
    assert progress.total_output_tokens == 20
    assert progress.status == SummarizationStatus.COMPLETED
    
    # Verify logs
    mock_logger.info.assert_any_call(f"Starting summarization for work {work_id}")
    mock_logger.info.assert_any_call(f"Selected 1 nodes for summarization")
    mock_logger.info.assert_any_call("Completed node 1/1: chunk_1")
    
    # Check for the completion message which includes timing
    # Since we can't match duration exactly, we check for the prefix
    completion_calls = [call for call in mock_logger.info.call_args_list if f"Summarization completed for work {work_id}" in call[0][0]]
    assert len(completion_calls) == 1
    
    mock_logger.info.assert_any_call(f"Total token usage for work {work_id}: input=10, output=20")

@patch("vulcanlab.summarize.llm_summarize.logger")
@patch("vulcanlab.summarize.llm_summarize.call_llm")
@patch("vulcanlab.summarize.llm_summarize.get_active_template")
def test_summarize_node_logging_and_tokens(mock_template, mock_call, mock_logger, db_session):
    # Setup
    evidence = EvidencePacket(heading_path="Intro", line_start=1, line_end=10)
    mock_template.return_value = "Template {heading_path} {line_range} {snippets} {keyphrases} {stats}"
    mock_call.return_value = ('{"gist": "summary"}', TokenUsage(input_tokens=100, output_tokens=50, model="gpt-4"))
    
    # Run
    summary = summarize_node(evidence, db_session, chunk_id="chunk_1")
    
    # Verify tokens
    assert summary.token_usage.input_tokens == 100
    assert summary.token_usage.output_tokens == 50
    
    # Verify logs
    mock_logger.debug.assert_any_call("Building prompt for node chunk_1, evidence snippets: 0")

@patch("vulcanlab.summarize.llm_summarize.logger")
@patch("vulcanlab.summarize.llm_summarize.call_llm")
@patch("vulcanlab.summarize.llm_summarize.get_active_template")
@patch("vulcanlab.summarize.llm_summarize.handle_escalation")
def test_summarize_node_escalation_logging(mock_escalate, mock_template, mock_call, mock_logger, db_session):
    # Setup
    evidence = EvidencePacket(heading_path="Intro", line_start=1, line_end=10)
    mock_template.return_value = "Template {heading_path} {line_range} {snippets} {keyphrases} {stats}"
    
    # First call returns insufficient_evidence
    # Second call (after escalation) returns success
    mock_call.side_effect = [
        ('{"gist": "poor", "insufficient_evidence": true, "missing_concepts": ["X"]}', 
         TokenUsage(input_tokens=50, output_tokens=10, model="gpt-4")),
        ('{"gist": "good", "insufficient_evidence": false}', 
         TokenUsage(input_tokens=60, output_tokens=20, model="gpt-4"))
    ]
    mock_escalate.return_value = "Some extra context"
    
    # Run
    summary = summarize_node(evidence, db_session, full_content="Full content", chunk_id="chunk_1")
    
    # Verify token aggregation (50+60, 10+20)
    assert summary.token_usage.input_tokens == 110
    assert summary.token_usage.output_tokens == 30
    
    # Verify escalation logs
    mock_logger.warning.assert_any_call("LLM returned insufficient_evidence for node chunk_1")
    mock_logger.info.assert_any_call("Escalation triggered for node chunk_1")

@patch("vulcanlab.summarize.compile.logger")
@patch("vulcanlab.summarize.compile.call_llm")
@patch("vulcanlab.summarize.compile.load_summary_nodes")
@patch("vulcanlab.summarize.compile.get_active_template")
@patch("vulcanlab.summarize.compile.Work")
def test_compile_logging(mock_work_cls, mock_template, mock_load_nodes, mock_call, mock_logger, db_session):
    from vulcanlab.summarize.compile import generate_derived_output
    from vulcanlab.data.models.work_summary import WorkSummaryType
    
    # Setup
    work_id = 456
    mock_work = MagicMock()
    mock_work.title = "Test Work"
    db_session.get.return_value = mock_work
    
    mock_node = MagicMock()
    mock_node.gist = "Node gist"
    mock_node.work_id = work_id
    mock_node.start_line = 1
    mock_node.end_line = 100
    mock_load_nodes.return_value = [mock_node]
    
    mock_template.return_value = "Template {work_title} {gists}"
    mock_call.return_value = ("Abstract content", TokenUsage(input_tokens=200, output_tokens=100, model="gpt-4"))
    
    # Run
    generate_derived_output(work_id, WorkSummaryType.ABSTRACT, db_session)
    
    # Verify logs
    mock_logger.info.assert_any_call(f"Generating {WorkSummaryType.ABSTRACT} for work {work_id}")
    mock_logger.info.assert_any_call(f"Derived output {WorkSummaryType.ABSTRACT} completed for work {work_id}")
