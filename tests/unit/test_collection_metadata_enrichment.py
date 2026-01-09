"""
Unit tests for collection item metadata enrichment.
"""

import pytest
from unittest.mock import MagicMock, patch
from fastapi import status, HTTPException

from vulcanlab.data.models.collection_item import CollectionItem
from vulcanlab.data.models.work import Work
from vulcanlab.data.models.chunk import Chunk
from vulcanlab.data.models.query import Query as QueryModel
from vulcanlab.data.models.result import Result
from vulcanlab_api.routers.collections import get_item_metadata


from vulcanlab.data.models.enums import CollectionItemType

@pytest.mark.asyncio
async def test_get_metadata_excerpt_success():
    """Test enriching metadata for an excerpt."""
    with patch('vulcanlab_api.routers.collections.get_session') as mock_get_session:
        mock_session = MagicMock()
        mock_get_session.return_value.__enter__.return_value = mock_session
        
        # Mock item
        item = CollectionItem(id=1, collection_id=1, item_type=CollectionItemType.EXCERPT, link="/search/result/10/100/200")
        mock_session.get.side_effect = lambda model, id: item if model == CollectionItem else (
            Work(id=10, title="Test Work", authors="Author", year=2023) if model == Work else None
        )
        
        # Mock chunk query
        chunk = Chunk(work_id=10, start_line=100, end_line=200, content="This is a test content that is long enough to be truncated if it was more than 75 words but it is not.", heading_breadcrumbs="H1 > H2")
        mock_session.execute.return_value.scalars.return_value.first.return_value = chunk
        
        response = await get_item_metadata(1, 1)
        
        assert response.type == "excerpt"
        assert response.title == "Test Work"
        assert response.heading_breadcrumbs == "H1 > H2"
        assert "test content" in response.excerpt_preview


@pytest.mark.asyncio
async def test_get_metadata_research_result_success():
    """Test enriching metadata for a research result."""
    with patch('vulcanlab_api.routers.collections.get_session') as mock_get_session:
        mock_session = MagicMock()
        mock_get_session.return_value.__enter__.return_value = mock_session
        
        item = CollectionItem(id=2, collection_id=1, item_type=CollectionItemType.RESEARCH_RESULT, link="/rag/5/results/50")
        
        def mock_get(model, id):
            if model == CollectionItem: return item
            if model == QueryModel: return QueryModel(id=5, original_query="What is test?")
            if model == Result: return Result(id=50, response_text="Test result content.")
            return None
            
        mock_session.get.side_effect = mock_get
        
        response = await get_item_metadata(1, 2)
        
        assert response.type == "research_result"
        assert response.query_text == "What is test?"
        assert response.content_preview == "Test result content."


@pytest.mark.asyncio
async def test_get_metadata_research_query_success():
    """Test enriching metadata for a research query."""
    with patch('vulcanlab_api.routers.collections.get_session') as mock_get_session:
        mock_session = MagicMock()
        mock_get_session.return_value.__enter__.return_value = mock_session
        
        item = CollectionItem(id=3, collection_id=1, item_type=CollectionItemType.RESEARCH_QUERY, link="/rag/5")
        
        def mock_get(model, id):
            if model == CollectionItem: return item
            if model == QueryModel: return QueryModel(id=5, original_query="What is test?")
            return None
            
        mock_session.get.side_effect = mock_get
        
        response = await get_item_metadata(1, 3)
        
        assert response.type == "research_query"
        assert response.query_text == "What is test?"


@pytest.mark.asyncio
async def test_get_metadata_source_deleted():
    """Test metadata enrichment when source work is deleted."""
    with patch('vulcanlab_api.routers.collections.get_session') as mock_get_session:
        mock_session = MagicMock()
        mock_get_session.return_value.__enter__.return_value = mock_session
        
        item = CollectionItem(id=1, collection_id=1, item_type=CollectionItemType.EXCERPT, link="/search/result/10/100/200")
        mock_session.get.side_effect = lambda model, id: item if model == CollectionItem else None
        
        response = await get_item_metadata(1, 1)
        
        assert response.title == "Source Deleted"
        assert "removed" in response.excerpt_preview

