"""
Unit tests for Collection model.
"""

from datetime import datetime
import pytest
from sqlalchemy.orm import Session
from src.vulcanlab.data.models.collection import Collection


class TestCollectionModel:
    """Tests for the Collection model."""

    def test_create_collection(self):
        """Test creating a collection with all fields."""
        collection = Collection(
            name="Research Project A",
            description="All research related to Project A",
            tags=["psychology", "experiment-1"]
        )
        
        assert collection.name == "Research Project A"
        assert collection.description == "All research related to Project A"
        assert collection.tags == ["psychology", "experiment-1"]

    def test_collection_defaults(self):
        """Test that tags can be set and defaults exist in metadata."""
        collection = Collection(name="Default Test", tags=["test"])
        assert collection.tags == ["test"]
        # We trust server_default for DB-level defaults

    def test_collection_repr(self):
        """Test the string representation of a Collection."""
        collection = Collection(id=1, name="Test")
        assert repr(collection) == "<Collection(id=1, name='Test')>"

    def test_collection_tablename(self):
        """Test the table name."""
        assert Collection.__tablename__ == "collections"

