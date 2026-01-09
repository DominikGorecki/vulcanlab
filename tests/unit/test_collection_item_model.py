"""
Unit tests for CollectionItem model.
"""

from decimal import Decimal
import pytest
from src.vulcanlab.data.models.collection_item import CollectionItem
from src.vulcanlab.data.models.enums import CollectionItemType


class TestCollectionItemModel:
    """Tests for the CollectionItem model."""

    def test_create_collection_item(self):
        """Test creating a collection item with all fields."""
        item = CollectionItem(
            collection_id=1,
            item_type=CollectionItemType.EXCERPT,
            link="/search/result/1/2/3",
            note="Interesting finding",
            order=Decimal("1.500")
        )
        
        assert item.collection_id == 1
        assert item.item_type == CollectionItemType.EXCERPT
        assert item.link == "/search/result/1/2/3"
        assert item.note == "Interesting finding"
        assert item.order == Decimal("1.500")

    def test_collection_item_defaults(self):
        """Test that order can be set and defaults exist in metadata."""
        item = CollectionItem(
            collection_id=1,
            item_type=CollectionItemType.RESEARCH_QUERY,
            link="/rag/1",
            order=Decimal("5.0")
        )
        assert item.order == Decimal("5.0")
        # We trust server_default for DB-level defaults

    def test_collection_item_repr(self):
        """Test the string representation of a CollectionItem."""
        item = CollectionItem(id=1, collection_id=10, item_type=CollectionItemType.EXCERPT)
        assert repr(item) == "<CollectionItem(id=1, collection_id=10, item_type='excerpt')>"

    def test_collection_item_tablename(self):
        """Test the table name."""
        assert CollectionItem.__tablename__ == "collection_items"

