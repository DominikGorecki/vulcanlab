"""
Unit tests for Work model.
"""

from datetime import datetime
from unittest.mock import patch

import pytest

from vulcanlab.data.models.work import Work


class TestWorkModel:
    """Tests for the Work model."""

    def test_work_repr(self):
        """Test Work model string representation."""
        work = Work(id=1, title="A Very Long Title That Should Be Truncated")
        repr_str = repr(work)
        assert "Work" in repr_str
        assert "id=1" in repr_str

    def test_work_required_fields(self):
        """Test that Work requires title."""
        work = Work(title="Test Title")
        assert work.title == "Test Title"

    def test_work_optional_fields(self):
        """Test that Work optional fields default to None."""
        work = Work(title="Test")
        assert work.authors is None
        assert work.year is None
        assert work.publisher is None
        assert work.isbn is None
        assert work.doi is None
        assert work.abstract is None
        assert work.source_path is None
        assert work.markdown_path is None
        assert work.work_type is None

    def test_work_all_fields(self):
        """Test Work with all fields populated."""
        work = Work(
            title="Psychology Handbook",
            authors="John Smith, Jane Doe",
            year=2023,
            publisher="Academic Press",
            isbn="978-0-123456-78-9",
            doi="10.1000/example",
            abstract="A comprehensive guide...",
            source_path="/path/to/source.pdf",
            markdown_path="/path/to/output.md",
            work_type="book"
        )

        assert work.title == "Psychology Handbook"
        assert work.authors == "John Smith, Jane Doe"
        assert work.year == 2023
        assert work.publisher == "Academic Press"
        assert work.isbn == "978-0-123456-78-9"
        assert work.doi == "10.1000/example"
        assert work.abstract == "A comprehensive guide..."
        assert work.source_path == "/path/to/source.pdf"
        assert work.markdown_path == "/path/to/output.md"
        assert work.work_type == "book"

    def test_work_tablename(self):
        """Test that Work uses correct table name."""
        assert Work.__tablename__ == "works"
