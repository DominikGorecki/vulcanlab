"""
Unit tests for SummaryNode model.
Implementation of Ticket: work-summarization.T03
"""

import pytest
from vulcanlab.data.models.summary_node import SummaryNode


class TestSummaryNodeCreation:
    """Test basic model creation and field values."""

    def test_create_summary_node_basic(self):
        """Test creating a SummaryNode with basic fields."""
        summary = SummaryNode(
            chunk_id=1,
            work_id=2,
            gist="Test gist",
            start_line=10,
            end_line=20,
            salience_score=0.85
        )

        assert summary.chunk_id == 1
        assert summary.work_id == 2
        assert summary.gist == "Test gist"
        assert summary.start_line == 10
        assert summary.end_line == 20
        assert summary.salience_score == 0.85
        
        # Default JSONB lists
        assert summary.key_points == []
        assert summary.definitions == []
        assert summary.key_terms == []
        assert summary.examples == []

    def test_create_summary_node_with_json_data(self):
        """Test creating a SummaryNode with JSON data fields."""
        key_points = [{"text": "Point 1", "start_line": 11, "end_line": 12}]
        definitions = [{"term": "T1", "definition": "D1", "start_line": 13, "end_line": 14}]
        key_terms = [{"term": "Term 1", "start_line": 15, "end_line": 16}]
        examples = [{"text": "Example 1", "start_line": 17, "end_line": 18}]
        
        summary = SummaryNode(
            chunk_id=1,
            work_id=1,
            gist="Gist",
            key_points=key_points,
            definitions=definitions,
            key_terms=key_terms,
            examples=examples,
            start_line=1,
            end_line=10,
            salience_score=0.5
        )

        assert summary.key_points == key_points
        assert summary.definitions == definitions
        assert summary.key_terms == key_terms
        assert summary.examples == examples

    def test_repr(self):
        """Test __repr__ method."""
        summary = SummaryNode(id=1, work_id=2, chunk_id=3)
        repr_str = repr(summary)
        assert "SummaryNode" in repr_str
        assert "id=1" in repr_str
        assert "work_id=2" in repr_str
        assert "chunk_id=3" in repr_str
