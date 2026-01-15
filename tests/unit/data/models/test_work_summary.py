"""
Unit tests for WorkSummary model and WorkSummaryType enum.
Implementation of Ticket: work-summarization.T03
"""

import pytest
from vulcanlab.data.models.work_summary import WorkSummary, WorkSummaryType


class TestWorkSummaryTypeEnum:
    """Test WorkSummaryType enum values."""

    def test_enum_values_are_lowercase(self):
        """Test that WorkSummaryType enum values match the database CHECK constraint (lowercase)."""
        assert WorkSummaryType.ABSTRACT == 'abstract'
        assert WorkSummaryType.OUTLINE == 'outline'
        assert WorkSummaryType.KEY_CONCEPTS == 'key_concepts'
        assert WorkSummaryType.CHAPTER_SUMMARIES == 'chapter_summaries'


class TestWorkSummaryCreation:
    """Test basic model creation and field values."""

    def test_create_work_summary_basic(self):
        """Test creating a WorkSummary with basic fields."""
        content = {"sections": [{"heading": "Introduction", "gist": "..."}]}
        line_refs = [{"start_line": 1, "end_line": 100}]
        
        summary = WorkSummary(
            work_id=1,
            type=WorkSummaryType.OUTLINE,
            content=content,
            line_references=line_refs
        )

        assert summary.work_id == 1
        assert summary.type == WorkSummaryType.OUTLINE
        assert summary.content == content
        assert summary.line_references == line_refs

    def test_repr(self):
        """Test __repr__ method."""
        summary = WorkSummary(id=1, work_id=2, type=WorkSummaryType.ABSTRACT)
        repr_str = repr(summary)
        assert "WorkSummary" in repr_str
        assert "id=1" in repr_str
        assert "work_id=2" in repr_str
        assert "type='abstract'" in repr_str
