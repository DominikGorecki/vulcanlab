"""
Unit tests for collections API endpoints.
"""

from datetime import datetime, timezone
import pytest
from unittest.mock import MagicMock, patch
from fastapi import status, HTTPException

from vulcanlab.data.models.collection import Collection
from vulcanlab_api.routers.collections import (
    list_collections,
    create_collection,
    get_collection,
    update_collection,
    delete_collection,
)
from vulcanlab_api.schemas.collections import (
    CollectionCreate,
    CollectionUpdate,
)


@pytest.fixture
def mock_now():
    return datetime.now(timezone.utc)


@pytest.mark.asyncio
async def test_list_collections_success(mock_now):
    """Test listing collections with pagination and filtering."""
    with patch('vulcanlab_api.routers.collections.get_session') as mock_get_session, \
         patch('vulcanlab_api.routers.collections.core_list_collections') as mock_core_list:
        
        mock_session = MagicMock()
        mock_get_session.return_value.__enter__.return_value = mock_session
        
        # Mock core return
        c1 = Collection(id=1, name="C1", tags=["tag1"], created_at=mock_now, updated_at=mock_now)
        c1.item_count = 5
        c2 = Collection(id=2, name="C2", tags=["tag2"], created_at=mock_now, updated_at=mock_now)
        c2.item_count = 0
        
        mock_core_list.return_value = ([c1, c2], 2)
        
        # When calling directly, we need to pass None for Query params if we want to match None in assert
        response = await list_collections(tag=None, search=None, page=1, page_size=10)
        
        assert response.total == 2
        assert len(response.collections) == 2
        assert response.collections[0].name == "C1"
        assert response.collections[0].item_count == 5
        assert response.collections[1].name == "C2"
        assert response.collections[1].item_count == 0
        
        mock_core_list.assert_called_once_with(
            session=mock_session,
            tag=None,
            search=None,
            skip=0,
            limit=10
        )


@pytest.mark.asyncio
async def test_create_collection_success(mock_now):
    """Test creating a collection."""
    with patch('vulcanlab_api.routers.collections.get_session') as mock_get_session, \
         patch('vulcanlab_api.routers.collections.core_create_collection') as mock_core_create, \
         patch('vulcanlab_api.routers.collections.core_get_collection') as mock_core_get:
        
        mock_session = MagicMock()
        mock_get_session.return_value.__enter__.return_value = mock_session
        
        # Created object
        created = Collection(id=1, name="New", description="Desc", tags=["t1"], created_at=mock_now, updated_at=mock_now)
        created.item_count = 0
        
        mock_core_create.return_value = created
        mock_core_get.return_value = created
        
        data = CollectionCreate(name="New", description="Desc", tags=["t1"])
        response = await create_collection(data)
        
        assert response.id == 1
        assert response.name == "New"
        assert response.item_count == 0
        mock_session.commit.assert_called_once()


@pytest.mark.asyncio
async def test_get_collection_success(mock_now):
    """Test getting a specific collection."""
    with patch('vulcanlab_api.routers.collections.get_session') as mock_get_session, \
         patch('vulcanlab_api.routers.collections.core_get_collection') as mock_core_get:
        
        mock_session = MagicMock()
        mock_get_session.return_value.__enter__.return_value = mock_session
        
        collection = Collection(id=1, name="C1", tags=[], created_at=mock_now, updated_at=mock_now)
        collection.item_count = 3
        mock_core_get.return_value = collection
        
        response = await get_collection(1)
        
        assert response.id == 1
        assert response.item_count == 3


@pytest.mark.asyncio
async def test_get_collection_not_found():
    """Test getting a non-existent collection."""
    with patch('vulcanlab_api.routers.collections.get_session') as mock_get_session, \
         patch('vulcanlab_api.routers.collections.core_get_collection') as mock_core_get:
        
        mock_session = MagicMock()
        mock_get_session.return_value.__enter__.return_value = mock_session
        mock_core_get.return_value = None
        
        with pytest.raises(HTTPException) as exc:
            await get_collection(999)
        
        assert exc.value.status_code == status.HTTP_404_NOT_FOUND


@pytest.mark.asyncio
async def test_update_collection_success(mock_now):
    """Test updating a collection."""
    with patch('vulcanlab_api.routers.collections.get_session') as mock_get_session, \
         patch('vulcanlab_api.routers.collections.core_update_collection') as mock_core_update, \
         patch('vulcanlab_api.routers.collections.core_get_collection') as mock_core_get:
        
        mock_session = MagicMock()
        mock_get_session.return_value.__enter__.return_value = mock_session
        
        updated = Collection(id=1, name="Updated", tags=["new"], created_at=mock_now, updated_at=mock_now)
        updated.item_count = 5
        
        mock_core_update.return_value = updated
        mock_core_get.return_value = updated
        
        data = CollectionUpdate(name="Updated", tags=["new"])
        response = await update_collection(1, data)
        
        assert response.name == "Updated"
        assert response.tags == ["new"]
        mock_session.commit.assert_called_once()


@pytest.mark.asyncio
async def test_delete_collection_success():
    """Test deleting a collection."""
    with patch('vulcanlab_api.routers.collections.get_session') as mock_get_session, \
         patch('vulcanlab_api.routers.collections.core_delete_collection') as mock_core_delete:
        
        mock_session = MagicMock()
        mock_get_session.return_value.__enter__.return_value = mock_session
        mock_core_delete.return_value = True
        
        await delete_collection(1)
        
        mock_session.commit.assert_called_once()
        mock_core_delete.assert_called_once_with(mock_session, 1)

