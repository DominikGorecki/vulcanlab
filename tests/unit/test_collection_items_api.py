"""
Unit tests for collection items API endpoints.
"""

from datetime import datetime, timezone
import pytest
from decimal import Decimal
from unittest.mock import MagicMock, patch
from fastapi import status, HTTPException

from vulcanlab.data.models.collection_item import CollectionItem
from vulcanlab.data.models.enums import CollectionItemType
from vulcanlab_api.routers.collections import (
    add_item,
    update_item,
    delete_item,
    bulk_delete_items,
    get_item_metadata,
)
from vulcanlab_api.schemas.collections import (
    CollectionItemCreate,
    CollectionItemUpdate,
    BulkDeleteRequest,
)


@pytest.fixture
def mock_now():
    return datetime.now(timezone.utc)


@pytest.mark.asyncio
async def test_add_item_success(mock_now):
    """Test adding an item to a collection."""
    with patch('vulcanlab_api.routers.collections.get_session') as mock_get_session, \
         patch('vulcanlab_api.routers.collections.core_add_item') as mock_core_add:
        
        mock_session = MagicMock()
        mock_get_session.return_value.__enter__.return_value = mock_session
        
        # Mock core return
        item = CollectionItem(
            id=1, 
            collection_id=1, 
            item_type=CollectionItemType.EXCERPT,
            link="/search/result/1/2/3",
            order=Decimal("1.0"),
            date_added=mock_now,
            last_modified=mock_now
        )
        mock_core_add.return_value = item
        
        # Mock session.get for collection existence check
        mock_session.get.return_value = MagicMock()
        
        data = CollectionItemCreate(
            item_type=CollectionItemType.EXCERPT,
            link="/search/result/1/2/3",
            order=Decimal("1.0")
        )
        response = await add_item(1, data)
        
        assert response.id == 1
        assert response.link == "/search/result/1/2/3"
        mock_session.commit.assert_called_once()


@pytest.mark.asyncio
async def test_add_item_invalid_link():
    """Test adding an item with an invalid link."""
    with patch('vulcanlab_api.routers.collections.get_session') as mock_get_session, \
         patch('vulcanlab_api.routers.collections.core_add_item') as mock_core_add:
        
        mock_session = MagicMock()
        mock_get_session.return_value.__enter__.return_value = mock_session
        mock_session.get.return_value = MagicMock()
        
        mock_core_add.side_effect = ValueError("Invalid link format")
        
        data = CollectionItemCreate(
            item_type=CollectionItemType.EXCERPT,
            link="/invalid/link"
        )
        
        with pytest.raises(HTTPException) as exc:
            await add_item(1, data)
        
        assert exc.value.status_code == status.HTTP_400_BAD_REQUEST
        assert "Invalid link format" in exc.value.detail


@pytest.mark.asyncio
async def test_update_item_success(mock_now):
    """Test updating a collection item."""
    with patch('vulcanlab_api.routers.collections.get_session') as mock_get_session, \
         patch('vulcanlab_api.routers.collections.core_update_item') as mock_core_update:
        
        mock_session = MagicMock()
        mock_get_session.return_value.__enter__.return_value = mock_session
        
        item = CollectionItem(
            id=10, 
            collection_id=1, 
            item_type=CollectionItemType.EXCERPT,
            link="/link",
            order=Decimal("2.0"),
            note="Updated note",
            date_added=mock_now,
            last_modified=mock_now
        )
        mock_core_update.return_value = item
        
        data = CollectionItemUpdate(note="Updated note", order=Decimal("2.0"))
        response = await update_item(1, 10, data)
        
        assert response.note == "Updated note"
        assert response.order == Decimal("2.0")
        mock_session.commit.assert_called_once()


@pytest.mark.asyncio
async def test_delete_item_success():
    """Test deleting a single item."""
    with patch('vulcanlab_api.routers.collections.get_session') as mock_get_session:
        mock_session = MagicMock()
        mock_get_session.return_value.__enter__.return_value = mock_session
        
        item = CollectionItem(id=10, collection_id=1)
        mock_session.get.return_value = item
        
        await delete_item(1, 10)
        
        mock_session.delete.assert_called_once_with(item)
        mock_session.commit.assert_called_once()


@pytest.mark.asyncio
async def test_bulk_delete_items_success():
    """Test bulk deleting items."""
    with patch('vulcanlab_api.routers.collections.get_session') as mock_get_session, \
         patch('vulcanlab_api.routers.collections.core_bulk_delete') as mock_core_bulk:
        
        mock_session = MagicMock()
        mock_get_session.return_value.__enter__.return_value = mock_session
        
        # Mock valid IDs check
        mock_session.execute.return_value.scalars.return_value.all.return_value = [1, 2]
        mock_core_bulk.return_value = 2
        
        request = BulkDeleteRequest(item_ids=[1, 2, 3]) # 3 is invalid or belongs to other
        response = await bulk_delete_items(1, request)
        
        assert response["deleted_count"] == 2
        mock_session.commit.assert_called_once()

