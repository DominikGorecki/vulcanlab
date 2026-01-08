"""
Unit tests for collections CRUD operations.
"""

from decimal import Decimal
import pytest
from unittest.mock import MagicMock, patch
from sqlalchemy.orm import Session

from src.vulcanlab.collections import (
    create_collection,
    get_collection,
    list_collections,
    update_collection,
    delete_collection,
    add_item_to_collection,
    update_collection_item,
    delete_collection_item,
    bulk_delete_collection_items
)
from src.vulcanlab.data.models.collection import Collection
from src.vulcanlab.data.models.collection_item import CollectionItem
from src.vulcanlab.data.models.enums import CollectionItemType


@pytest.fixture
def mock_session():
    return MagicMock(spec=Session)


class TestCollectionsCRUD:
    """Tests for collection CRUD operations using a mocked session."""

    def test_create_collection(self, mock_session):
        name = "Test Collection"
        description = "Test Description"
        tags = ["tag1", "tag2"]
        
        collection = create_collection(mock_session, name, description, tags)
        
        assert collection.name == name
        assert collection.description == description
        assert collection.tags == tags
        mock_session.add.assert_called_once()
        mock_session.flush.assert_called_once()

    def test_get_collection(self, mock_session):
        expected_collection = Collection(id=1, name="Test")
        # Mock session.execute().first() to return (collection, item_count)
        mock_execute = MagicMock()
        mock_execute.first.return_value = (expected_collection, 5)
        mock_session.execute.return_value = mock_execute
        
        result = get_collection(mock_session, 1)
        
        assert result == expected_collection
        assert result.item_count == 5

    def test_list_collections(self, mock_session):
        c1 = Collection(id=1, name="C1")
        c2 = Collection(id=2, name="C2")
        
        # Mocking the execution result for scalar_one() and all()
        mock_execute_count = MagicMock()
        mock_execute_count.scalar_one.return_value = 2
        
        mock_execute_data = MagicMock()
        mock_execute_data.all.return_value = [(c1, 5), (c2, 0)]
        
        mock_session.execute.side_effect = [mock_execute_count, mock_execute_data]
        
        results, total = list_collections(mock_session)
        
        assert total == 2
        assert len(results) == 2
        assert results[0] == c1
        assert results[0].item_count == 5
        assert results[1] == c2
        assert results[1].item_count == 0

    def test_update_collection(self, mock_session):
        collection = Collection(id=1, name="Old Name")
        
        # Mock get_collection inside update_collection
        mock_execute = MagicMock()
        mock_execute.first.return_value = (collection, 0)
        mock_session.execute.return_value = mock_execute
        
        updated = update_collection(mock_session, 1, name="New Name", tags=["new"])
        
        assert updated.name == "New Name"
        assert updated.tags == ["new"]

    def test_delete_collection(self, mock_session):
        collection = Collection(id=1)
        
        # Mock get_collection inside delete_collection
        mock_execute = MagicMock()
        mock_execute.first.return_value = (collection, 0)
        mock_session.execute.return_value = mock_execute
        
        result = delete_collection(mock_session, 1)
        
        assert result is True
        mock_session.delete.assert_called_once_with(collection)

    def test_add_item_to_collection(self, mock_session):
        collection_id = 1
        item_type = CollectionItemType.EXCERPT
        link = "/search/result/1/2/3"
        
        # Mock max_order query with a decimal value
        # 12.8 -> 14
        mock_execute = MagicMock()
        mock_execute.scalar.return_value = Decimal("12.8")
        mock_session.execute.return_value = mock_execute
        
        item = add_item_to_collection(mock_session, collection_id, item_type, link)
        
        assert item.collection_id == collection_id
        assert item.item_type == item_type
        assert item.link == link
        assert item.order == Decimal("14")
        mock_session.add.assert_called_once()

    def test_add_item_first_in_collection(self, mock_session):
        collection_id = 1
        item_type = CollectionItemType.EXCERPT
        link = "/search/result/1/2/3"
        
        # Mock max_order query returning None (empty collection)
        mock_execute = MagicMock()
        mock_execute.scalar.return_value = None
        mock_session.execute.return_value = mock_execute
        
        item = add_item_to_collection(mock_session, collection_id, item_type, link)
        
        assert item.order == Decimal("1")
        mock_session.add.assert_called_once()

    def test_add_item_invalid_link(self, mock_session):
        with pytest.raises(ValueError, match="Invalid link format"):
            add_item_to_collection(mock_session, 1, CollectionItemType.EXCERPT, "/invalid")

    def test_update_collection_item(self, mock_session):
        item = CollectionItem(id=1, note="Old")
        mock_session.get.return_value = item
        
        updated = update_collection_item(mock_session, 1, note="New", order=Decimal("5.5"))
        
        assert updated.note == "New"
        assert updated.order == Decimal("5.5")

    def test_delete_collection_item(self, mock_session):
        item = CollectionItem(id=1)
        mock_session.get.return_value = item
        
        result = delete_collection_item(mock_session, 1)
        
        assert result is True
        mock_session.delete.assert_called_once_with(item)

    def test_bulk_delete_items(self, mock_session):
        mock_execute = MagicMock()
        mock_execute.rowcount = 3
        mock_session.execute.return_value = mock_execute
        
        count = bulk_delete_collection_items(mock_session, [1, 2, 3])
        
        assert count == 3
        mock_session.execute.assert_called_once()

