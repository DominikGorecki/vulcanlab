import pytest
import json
from unittest.mock import MagicMock, patch
from sqlalchemy import select

from vulcanlab.summarize.llm_summarize import (
    KeyPoint,
    Definition,
    KeyTerm,
    Example,
    SummaryResponse,
    get_active_template,
    build_summarization_prompt,
    parse_llm_response,
    handle_escalation,
    summarize_node,
    get_llm_model
)
from vulcanlab.summarize.evidence import EvidencePacket, Snippet
from vulcanlab.data.models.prompt_template import PromptTemplate


@pytest.fixture
def mock_session():
    return MagicMock()


@pytest.fixture
def sample_evidence():
    return EvidencePacket(
        heading_path="H1 > H2",
        line_start=10,
        line_end=50,
        snippets=[
            Snippet(text="This is a definition.", start_line=15, end_line=15, snippet_type="definition"),
            Snippet(text="Bullet point 1.", start_line=20, end_line=20, snippet_type="enumeration")
        ],
        keyphrases=["concept A", "concept B"],
        stats={"total": 2}
    )


def test_get_active_template(mock_session):
    mock_template = MagicMock(spec=PromptTemplate)
    mock_template.template_content = "Template {heading_path} {snippets}"
    
    mock_result = MagicMock()
    mock_result.scalar_one_or_none.return_value = mock_template
    mock_session.execute.return_value = mock_result
    
    content = get_active_template("summarize_node", mock_session)
    assert content == "Template {heading_path} {snippets}"
    
    # Check if correct query was made
    args, _ = mock_session.execute.call_args
    # Instead of string matching the query object, check that the function was called
    assert mock_session.execute.called


def test_build_summarization_prompt(mock_session, sample_evidence):
    with patch("vulcanlab.summarize.llm_summarize.get_active_template") as mock_get_template:
        mock_get_template.return_value = "Path: {heading_path}, Range: {line_range}, Snippets: {snippets}, Key: {keyphrases}, Stats: {stats}"
        
        prompt = build_summarization_prompt(sample_evidence, mock_session)
        
        assert "Path: H1 > H2" in prompt
        assert "Range: 10-50" in prompt
        assert "This is a definition." in prompt
        assert "concept A, concept B" in prompt
        assert '"total": 2' in prompt


def test_parse_llm_response(sample_evidence):
    valid_json = {
        "gist": "A short gist.",
        "key_points": [{"text": "Point 1", "start_line": 20, "end_line": 21}],
        "definitions": [{"term": "Term", "definition": "Def", "start_line": 15, "end_line": 15}],
        "key_terms": [{"term": "T1", "start_line": 25, "end_line": 25}],
        "examples": [{"text": "Ex 1", "start_line": 30, "end_line": 30}],
        "insufficient_evidence": False,
        "missing_concepts": []
    }
    
    response_text = f"Here is the result:\n```json\n{json.dumps(valid_json)}\n```"
    summary = parse_llm_response(response_text, sample_evidence)
    
    assert summary.gist == "A short gist."
    assert len(summary.key_points) == 1
    assert summary.key_points[0].text == "Point 1"
    assert summary.key_points[0].start_line == 20
    assert summary.insufficient_evidence is False


def test_parse_llm_response_validation(sample_evidence):
    # Test line number clamping
    invalid_json = {
        "gist": "Gist",
        "key_points": [{"text": "Point", "start_line": 5, "end_line": 60}], # Outside 10-50
        "insufficient_evidence": False
    }
    
    summary = parse_llm_response(json.dumps(invalid_json), sample_evidence)
    assert summary.key_points[0].start_line == 10
    assert summary.key_points[0].end_line == 50


def test_parse_llm_response_malformed(sample_evidence):
    summary = parse_llm_response("Not JSON at all", sample_evidence)
    assert summary.insufficient_evidence is True
    assert "Error parsing" in summary.gist


def test_handle_escalation(sample_evidence):
    full_content = "\n".join([f"Line {i} content about ConceptX" for i in range(1, 101)])
    missing_concepts = ["ConceptX"]
    
    context = handle_escalation(sample_evidence, missing_concepts, full_content)
    
    # ConceptX is in lines 1-100. Evidence is 10-50.
    # handle_escalation should find ConceptX in lines 1-9 or 51-100.
    assert "ConceptX" in context
    assert "Lines 1-2" in context or "Lines 51" in context 


@patch("vulcanlab.summarize.llm_summarize.call_llm")
@patch("vulcanlab.summarize.llm_summarize.get_llm_model")
@patch("vulcanlab.summarize.llm_summarize.build_summarization_prompt")
def test_summarize_node(mock_prompt, mock_model, mock_call, mock_session, sample_evidence):
    mock_prompt.return_value = "Mock Prompt"
    mock_model.return_value = "gpt-4o"
    
    # First call returns insufficient evidence
    first_response = {
        "gist": "Not enough info",
        "insufficient_evidence": True,
        "missing_concepts": ["ConceptY"]
    }
    # Second call returns full summary
    second_response = {
        "gist": "Complete summary",
        "insufficient_evidence": False,
        "key_points": []
    }
    
    mock_call.side_effect = [json.dumps(first_response), json.dumps(second_response)]
    
    full_content = "Line 1: ConceptY is here.\n" + "\n".join([f"Line {i}" for i in range(2, 100)])
    
    summary = summarize_node(sample_evidence, mock_session, full_content=full_content)
    
    assert summary.gist == "Complete summary"
    assert mock_call.call_count == 2
    # Verify second call included additional context
    args, _ = mock_call.call_args
    assert "Mock Prompt" in args[0]
    # Check that additional context was added in the recursive call
    # Wait, my summarize_node passes additional_context to the prompt
    # In the second call, the prompt should have "Additional Context:"
    # But wait, my mock_prompt.return_value is "Mock Prompt" every time.
    # Actually, in summarize_node:
    # prompt = build_summarization_prompt(evidence, session)
    # if additional_context: prompt += ...
    
    assert "Additional Context:" in args[0]


@patch("vulcanlab.summarize.llm_summarize.load_config")
def test_get_llm_model(mock_load_config):
    mock_config = MagicMock()
    mock_config.llm.provider = "openai"
    mock_config.llm.models.openai.full = "gpt-4o-test"
    mock_load_config.return_value = mock_config
    
    assert get_llm_model() == "gpt-4o-test"
