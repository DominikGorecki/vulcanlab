import pytest
import json
from unittest.mock import MagicMock, patch
from sqlalchemy import select

from vulcanlab.summarize.compile import (
    load_summary_nodes,
    compile_abstract,
    compile_outline,
    compile_key_concepts,
    compile_chapter_summaries,
    generate_derived_output,
    get_derived_outputs
)
from vulcanlab.data.models.summary_node import SummaryNode
from vulcanlab.data.models.work_summary import WorkSummary, WorkSummaryType
from vulcanlab.data.models.work import Work
from vulcanlab.data.models.chunk import Chunk


@pytest.fixture
def mock_session():
    return MagicMock()


@pytest.fixture
def sample_work():
    work = MagicMock(spec=Work)
    work.id = 1
    work.title = "Test Psychology Work"
    return work


@pytest.fixture
def sample_nodes(sample_work):
    node1 = MagicMock(spec=SummaryNode)
    node1.id = 1
    node1.work_id = sample_work.id
    node1.gist = "Gist of first node."
    node1.start_line = 10
    node1.end_line = 20
    node1.definitions = [
        {"term": "Cognition", "definition": "Mental action.", "start_line": 12, "end_line": 12}
    ]
    node1.key_terms = [{"term": "Mind", "start_line": 15, "end_line": 15}]
    
    chunk1 = MagicMock(spec=Chunk)
    chunk1.level = "H1"
    chunk1.heading_breadcrumbs = "Introduction"
    node1.chunk = chunk1

    node2 = MagicMock(spec=SummaryNode)
    node2.id = 2
    node2.work_id = sample_work.id
    node2.gist = "Gist of second node."
    node2.start_line = 21
    node2.end_line = 30
    node2.definitions = [
        {"term": "cognition", "definition": "Mental process of acquiring knowledge.", "start_line": 25, "end_line": 25}
    ]
    node2.key_terms = []
    
    chunk2 = MagicMock(spec=Chunk)
    chunk2.level = "H2"
    chunk2.heading_breadcrumbs = "Introduction > Background"
    node2.chunk = chunk2

    return [node1, node2]


def test_load_summary_nodes(mock_session):
    mock_result = MagicMock()
    mock_result.scalars.return_value.all.return_value = ["node1", "node2"]
    mock_session.execute.return_value = mock_result
    
    nodes = load_summary_nodes(1, mock_session)
    assert nodes == ["node1", "node2"]
    assert mock_session.execute.called


@patch("vulcanlab.summarize.compile.call_llm")
@patch("vulcanlab.summarize.compile.get_active_template")
@patch("vulcanlab.summarize.compile.get_llm_model")
def test_compile_abstract(mock_model, mock_template, mock_call, mock_session, sample_nodes, sample_work):
    mock_model.return_value = "gpt-4o"
    mock_template.return_value = "Synthesize this: {work_title}\n{gists}"
    mock_call.return_value = "This is a synthesized abstract."
    
    summary = compile_abstract(sample_nodes, sample_work.title, mock_session)
    
    assert summary.type == WorkSummaryType.ABSTRACT
    assert summary.content["abstract"] == "This is a synthesized abstract."
    assert summary.line_references == [{"start_line": 10, "end_line": 30}]
    assert "Test Psychology Work" in mock_call.call_args[0][0]
    assert "Gist of first node." in mock_call.call_args[0][0]


def test_compile_outline(mock_session, sample_nodes):
    summary = compile_outline(sample_nodes, mock_session)
    
    assert summary.type == WorkSummaryType.OUTLINE
    outline = summary.content["outline"]
    assert len(outline) == 1 # H1 is root
    assert outline[0]["heading"] == "Introduction"
    assert len(outline[0]["children"]) == 1
    assert outline[0]["children"][0]["heading"] == "Background"
    assert outline[0]["children"][0]["gist"] == "Gist of second node."


@patch("vulcanlab.summarize.compile.call_llm")
@patch("vulcanlab.summarize.compile.get_active_template")
@patch("vulcanlab.summarize.compile.get_llm_model")
def test_compile_key_concepts(mock_model, mock_template, mock_call, mock_session, sample_nodes, sample_work):
    mock_model.return_value = "gpt-4o"
    mock_template.return_value = "Organize: {concepts}"
    
    llm_response = [
        {"term": "Cognition", "definition": "Refined mental process definition."}
    ]
    mock_call.return_value = json.dumps(llm_response)
    
    summary = compile_key_concepts(sample_nodes, sample_work.title, mock_session)
    
    assert summary.type == WorkSummaryType.KEY_CONCEPTS
    concepts = summary.content["key_concepts"]
    assert len(concepts) == 1
    assert concepts[0]["term"] == "Cognition"
    # Verify occurrences were re-attached
    assert len(concepts[0]["occurrences"]) == 2
    assert concepts[0]["occurrences"][0]["start_line"] == 12


def test_compile_chapter_summaries(mock_session, sample_nodes):
    summary = compile_chapter_summaries(sample_nodes, mock_session)
    
    assert summary.type == WorkSummaryType.CHAPTER_SUMMARIES
    chapters = summary.content["chapters"]
    assert len(chapters) == 2 # Both H1 and H2 are included
    assert chapters[0]["heading"] == "Introduction"
    assert chapters[1]["heading"] == "Background"
    assert chapters[0]["level"] == "H1"
    assert chapters[1]["level"] == "H2"


@patch("vulcanlab.summarize.compile.load_summary_nodes")
@patch("vulcanlab.summarize.compile.compile_outline")
def test_generate_derived_output_upsert(mock_compile, mock_load, mock_session, sample_work, sample_nodes):
    mock_session.get.return_value = sample_work
    mock_load.return_value = sample_nodes
    
    # 1. Test creation (no existing)
    mock_session.execute.return_value.scalar_one_or_none.return_value = None
    
    new_summary = MagicMock(spec=WorkSummary)
    new_summary.content = {"outline": []}
    new_summary.line_references = []
    new_summary.work_id = sample_work.id
    new_summary.type = WorkSummaryType.OUTLINE
    mock_compile.return_value = new_summary
    
    result = generate_derived_output(sample_work.id, WorkSummaryType.OUTLINE, mock_session)
    
    assert result == new_summary
    assert mock_session.add.called
    
    # 2. Test update (existing)
    existing_summary = MagicMock(spec=WorkSummary)
    mock_session.execute.return_value.scalar_one_or_none.return_value = existing_summary
    
    result = generate_derived_output(sample_work.id, WorkSummaryType.OUTLINE, mock_session)
    
    assert result == existing_summary
    assert existing_summary.content == new_summary.content
    assert not (mock_session.add.call_count > 1)


def test_get_derived_outputs(mock_session):
    mock_result = MagicMock()
    mock_result.scalars.return_value.all.return_value = ["s1", "s2"]
    mock_session.execute.return_value = mock_result
    
    outputs = get_derived_outputs(1, mock_session)
    assert outputs == ["s1", "s2"]
