"""
Unit tests for the context assembler module.
"""

import pytest
from unittest.mock import MagicMock, patch
from decimal import Decimal

from vulcanlab.research.context_assembler import (
    fetch_collection_items,
    deduplicate_content,
    apply_token_limit,
    build_source_attribution,
    assemble_context_for_question
)
from vulcanlab.data.models.enums import CollectionItemType
from vulcanlab.data.models.collection_item import CollectionItem
from vulcanlab.data.models.work import Work
from vulcanlab.data.models.chunk import Chunk
from vulcanlab.data.models.query import Query
from vulcanlab.data.models.result import Result

@pytest.fixture
def mock_session():
    return MagicMock()

def test_fetch_collection_items_excerpt(mock_session):
    # Mock data
    item = CollectionItem(id=1, item_type=CollectionItemType.EXCERPT, link="/search/result/10/100/200")
    work = Work(id=10, title="Test Work", authors="Test Author", year=2023)
    chunk1 = Chunk(content="Part 1", start_line=100, end_line=150, heading_breadcrumbs="H1")
    chunk2 = Chunk(content="Part 2", start_line=151, end_line=200, heading_breadcrumbs="H1")
    
    mock_session.execute.return_value.scalars.return_value.all.side_effect = [
        [item], # CollectionItem query
        [chunk1, chunk2] # Chunks query
    ]
    mock_session.get.return_value = work
    
    results = fetch_collection_items([1], mock_session)
    
    assert len(results) == 1
    assert results[0]["item_id"] == 1
    assert results[0]["type"] == "excerpt"
    assert "Part 1\n\nPart 2" in results[0]["content"]
    assert results[0]["work_metadata"]["title"] == "Test Work"

def test_fetch_collection_items_research_result(mock_session):
    item = CollectionItem(id=2, item_type=CollectionItemType.RESEARCH_RESULT, link="/rag/5/results/50")
    result_rec = Result(id=50, response_text="Detailed research result.")
    
    mock_session.execute.return_value.scalars.return_value.all.return_value = [item]
    mock_session.get.return_value = result_rec
    
    results = fetch_collection_items([2], mock_session)
    
    assert len(results) == 1
    assert results[0]["type"] == "research_result"
    assert results[0]["content"] == "Detailed research result."

def test_fetch_collection_items_research_query(mock_session):
    item = CollectionItem(id=3, item_type=CollectionItemType.RESEARCH_QUERY, link="/rag/5")
    query_rec = Query(id=5, original_query="What is the meaning of life?")
    
    mock_session.execute.return_value.scalars.return_value.all.return_value = [item]
    mock_session.get.return_value = query_rec
    
    results = fetch_collection_items([3], mock_session)
    
    assert len(results) == 1
    assert results[0]["type"] == "research_query"
    assert results[0]["content"] == "What is the meaning of life?"

def test_deduplicate_content_exact_duplicate():
    items = [
        {"item_id": 1, "type": "excerpt", "content": "Duplicate content", "work_metadata": {"work_id": 10}},
        {"item_id": 2, "type": "excerpt", "content": "Duplicate content", "work_metadata": {"work_id": 10}}
    ]
    
    deduped = deduplicate_content(items)
    assert len(deduped) == 1

def test_deduplicate_content_overlap():
    items = [
        {"item_id": 1, "type": "excerpt", "content": "This is a long sentence that is repeated.", "work_metadata": {"work_id": 10}},
        {"item_id": 2, "type": "excerpt", "content": "This is a long sentence that is repeated. Plus some extra.", "work_metadata": {"work_id": 10}}
    ]
    
    deduped = deduplicate_content(items)
    assert len(deduped) == 1
    assert "Plus some extra" in deduped[0]["content"]

def test_apply_token_limit():
    content = "word " * 100
    # Mock tiktoken to return 100 tokens
    with patch("tiktoken.encoding_for_model") as mock_enc:
        mock_encoding = MagicMock()
        mock_encoding.encode.return_value = list(range(100))
        mock_encoding.decode.return_value = "truncated content"
        mock_enc.return_value = mock_encoding
        
        # Test no truncation
        truncated, count = apply_token_limit(content, max_tokens=150)
        assert count == 100
        assert truncated == content
        
        # Test truncation
        truncated, count = apply_token_limit(content, max_tokens=50)
        assert count == 50
        assert "...[truncated]" in truncated

def test_build_source_attribution():
    items = [
        {
            "item_id": 1,
            "type": "excerpt",
            "content": "Some content",
            "work_metadata": {"work_id": 10, "title": "Work Title"}
        },
        {
            "item_id": 2,
            "type": "research_result",
            "content": "Result content",
            "work_metadata": None
        }
    ]
    
    sources = build_source_attribution(items)
    assert len(sources) == 2
    assert sources[0]["work_title"] == "Work Title"
    assert sources[1]["type"] == "research_result"
    assert sources[1]["work_id"] is None

def test_assemble_context_for_question_new_generation(mock_session):
    # Mock fetch_collection_items
    item1 = {"item_id": 1, "type": "excerpt", "content": "Excerpt content", "work_metadata": {"work_id": 10, "title": "T", "authors": "A", "year": 2023}}
    
    with patch("vulcanlab.research.context_assembler.fetch_collection_items") as mock_fetch:
        mock_fetch.return_value = [item1]
        
        result = assemble_context_for_question(1, [1], session=mock_session)
        
        assert "Excerpt content" in result["context"]
        assert "Source: EXCERPT" in result["context"]
        assert len(result["sources"]) == 1
        assert result["sources"][0]["item_id"] == 1

def test_assemble_context_for_question_reuse(mock_session):
    # Mock Results
    res1 = Result(id=50, response_text="Reused result content")
    mock_session.execute.return_value.scalars.return_value.all.return_value = [res1]
    
    reuse_info = {"source_result_ids": [50]}
    
    result = assemble_context_for_question(1, [], reuse_info=reuse_info, session=mock_session)
    
    assert "Reused result content" in result["context"]
    assert len(result["sources"]) == 1
    assert result["sources"][0]["type"] == "research_result"
    assert "work_title" in result["sources"][0]
