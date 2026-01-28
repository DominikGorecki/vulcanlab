"""
Unit tests for the combine module.

Tests the combine_sections function.

Usage:
    pytest tests/unit/expansion/test_combine.py -v
"""

import pytest
from unittest.mock import MagicMock

from vulcanlab.expansion.combine import combine_sections
from vulcanlab.data.models.expansion import (
    AnswerExpansion,
    ExpansionSection,
    ExpansionStatus,
    SectionStatus,
)


class TestCombineSections:
    """Tests for combine_sections function."""

    def test_expansion_not_found_raises(self):
        """Test that combine_sections raises if expansion not found."""
        mock_session = MagicMock()
        mock_session.query.return_value.filter.return_value.first.return_value = None

        with pytest.raises(ValueError) as exc_info:
            combine_sections(expansion_id=999, session=mock_session)

        assert "not found" in str(exc_info.value)

    def test_no_sections_raises(self):
        """Test that combine_sections raises if expansion has no sections."""
        mock_session = MagicMock()

        mock_expansion = MagicMock(spec=AnswerExpansion)
        mock_expansion.id = 1
        mock_expansion.query_id = 10
        mock_expansion.result_id = 5
        mock_expansion.status = ExpansionStatus.BREAKDOWN_COMPLETE

        # First call returns expansion, second call returns empty sections
        mock_session.query.return_value.filter.return_value.first.return_value = mock_expansion
        mock_session.query.return_value.filter.return_value.order_by.return_value.all.return_value = []

        with pytest.raises(ValueError) as exc_info:
            combine_sections(expansion_id=1, session=mock_session)

        assert "no sections" in str(exc_info.value)

    def test_incomplete_sections_raises(self):
        """Test that combine_sections raises if sections not all completed."""
        mock_session = MagicMock()

        mock_expansion = MagicMock(spec=AnswerExpansion)
        mock_expansion.id = 1
        mock_expansion.query_id = 10
        mock_expansion.result_id = 5
        mock_expansion.status = ExpansionStatus.BREAKDOWN_COMPLETE

        mock_section1 = MagicMock(spec=ExpansionSection)
        mock_section1.order = 1
        mock_section1.status = SectionStatus.COMPLETED

        mock_section2 = MagicMock(spec=ExpansionSection)
        mock_section2.order = 2
        mock_section2.status = SectionStatus.READY  # Not completed

        mock_section3 = MagicMock(spec=ExpansionSection)
        mock_section3.order = 3
        mock_section3.status = SectionStatus.PENDING  # Not completed

        mock_session.query.return_value.filter.return_value.first.return_value = mock_expansion
        mock_session.query.return_value.filter.return_value.order_by.return_value.all.return_value = [
            mock_section1, mock_section2, mock_section3
        ]

        with pytest.raises(ValueError) as exc_info:
            combine_sections(expansion_id=1, session=mock_session)

        assert "not completed" in str(exc_info.value)
        assert "#2" in str(exc_info.value)
        assert "#3" in str(exc_info.value)

    def test_combine_sections_builds_report(self):
        """Test that combine_sections builds markdown report with headings."""
        mock_session = MagicMock()

        mock_expansion = MagicMock(spec=AnswerExpansion)
        mock_expansion.id = 1
        mock_expansion.query_id = 10
        mock_expansion.result_id = 5
        mock_expansion.status = ExpansionStatus.BREAKDOWN_COMPLETE

        mock_section1 = MagicMock(spec=ExpansionSection)
        mock_section1.order = 1
        mock_section1.heading = "Introduction"
        mock_section1.summary = "Overview of the topic"
        mock_section1.status = SectionStatus.COMPLETED
        mock_section1.response_text = "This is the introduction content."

        mock_section2 = MagicMock(spec=ExpansionSection)
        mock_section2.order = 2
        mock_section2.heading = "Main Content"
        mock_section2.summary = "Detailed explanation"
        mock_section2.status = SectionStatus.COMPLETED
        mock_section2.response_text = "This is the main content."

        mock_section3 = MagicMock(spec=ExpansionSection)
        mock_section3.order = 3
        mock_section3.heading = "Conclusion"
        mock_section3.summary = "Summary and final thoughts"
        mock_section3.status = SectionStatus.COMPLETED
        mock_section3.response_text = "This is the conclusion."

        mock_session.query.return_value.filter.return_value.first.return_value = mock_expansion
        mock_session.query.return_value.filter.return_value.order_by.return_value.all.return_value = [
            mock_section1, mock_section2, mock_section3
        ]

        result = combine_sections(expansion_id=1, session=mock_session)

        # Verify report structure
        assert "## Introduction" in result
        assert "## Main Content" in result
        assert "## Conclusion" in result

        # Verify content
        assert "This is the introduction content." in result
        assert "This is the main content." in result
        assert "This is the conclusion." in result

        # Verify summaries (italicized)
        assert "*Overview of the topic*" in result

        # Verify expansion status updated
        assert mock_expansion.status == ExpansionStatus.COMPLETED
        assert mock_expansion.combined_report == result

    def test_combine_sections_includes_original_link(self):
        """Test that combine_sections includes link to original answer."""
        mock_session = MagicMock()

        mock_expansion = MagicMock(spec=AnswerExpansion)
        mock_expansion.id = 1
        mock_expansion.query_id = 42
        mock_expansion.result_id = 17
        mock_expansion.status = ExpansionStatus.BREAKDOWN_COMPLETE

        mock_section = MagicMock(spec=ExpansionSection)
        mock_section.order = 1
        mock_section.heading = "Test Section"
        mock_section.summary = ""
        mock_section.status = SectionStatus.COMPLETED
        mock_section.response_text = "Content"

        mock_session.query.return_value.filter.return_value.first.return_value = mock_expansion
        mock_session.query.return_value.filter.return_value.order_by.return_value.all.return_value = [
            mock_section
        ]

        result = combine_sections(expansion_id=1, session=mock_session)

        # Verify link format
        assert "[View Original Answer]" in result
        assert "/rag/42/results/17" in result

    def test_combine_sections_handles_empty_summary(self):
        """Test that combine_sections handles sections with empty summary."""
        mock_session = MagicMock()

        mock_expansion = MagicMock(spec=AnswerExpansion)
        mock_expansion.id = 1
        mock_expansion.query_id = 10
        mock_expansion.result_id = 5
        mock_expansion.status = ExpansionStatus.BREAKDOWN_COMPLETE

        mock_section = MagicMock(spec=ExpansionSection)
        mock_section.order = 1
        mock_section.heading = "Test Section"
        mock_section.summary = ""  # Empty summary
        mock_section.status = SectionStatus.COMPLETED
        mock_section.response_text = "Section content."

        mock_session.query.return_value.filter.return_value.first.return_value = mock_expansion
        mock_session.query.return_value.filter.return_value.order_by.return_value.all.return_value = [
            mock_section
        ]

        result = combine_sections(expansion_id=1, session=mock_session)

        # Should not have empty italics
        assert "**" not in result  # No malformed markdown
        assert "## Test Section" in result
        assert "Section content." in result

    def test_combine_sections_handles_empty_response(self):
        """Test that combine_sections handles sections with no response."""
        mock_session = MagicMock()

        mock_expansion = MagicMock(spec=AnswerExpansion)
        mock_expansion.id = 1
        mock_expansion.query_id = 10
        mock_expansion.result_id = 5
        mock_expansion.status = ExpansionStatus.BREAKDOWN_COMPLETE

        mock_section = MagicMock(spec=ExpansionSection)
        mock_section.order = 1
        mock_section.heading = "Missing Response"
        mock_section.summary = "Summary"
        mock_section.status = SectionStatus.COMPLETED
        mock_section.response_text = None  # No response

        mock_session.query.return_value.filter.return_value.first.return_value = mock_expansion
        mock_session.query.return_value.filter.return_value.order_by.return_value.all.return_value = [
            mock_section
        ]

        result = combine_sections(expansion_id=1, session=mock_session)

        assert "## Missing Response" in result
        assert "(No response available)" in result

    def test_combine_sections_failure_sets_status(self):
        """Test that combine_sections sets FAILED status on error."""
        mock_session = MagicMock()

        mock_expansion = MagicMock(spec=AnswerExpansion)
        mock_expansion.id = 1
        mock_expansion.query_id = 10
        mock_expansion.result_id = 5
        mock_expansion.status = ExpansionStatus.BREAKDOWN_COMPLETE
        mock_expansion.expansion_metadata = None

        # Make query raise an exception
        mock_session.query.return_value.filter.return_value.first.return_value = mock_expansion
        mock_session.query.return_value.filter.return_value.order_by.return_value.all.side_effect = Exception("DB error")

        with pytest.raises(Exception):
            combine_sections(expansion_id=1, session=mock_session)

        assert mock_expansion.status == ExpansionStatus.FAILED

    def test_combine_sections_preserves_order(self):
        """Test that combine_sections preserves section order in report."""
        mock_session = MagicMock()

        mock_expansion = MagicMock(spec=AnswerExpansion)
        mock_expansion.id = 1
        mock_expansion.query_id = 10
        mock_expansion.result_id = 5
        mock_expansion.status = ExpansionStatus.BREAKDOWN_COMPLETE

        # Create sections (returned in order by order_by)
        sections = []
        for i in range(1, 6):
            s = MagicMock(spec=ExpansionSection)
            s.order = i
            s.heading = f"Section {i}"
            s.summary = f"Summary {i}"
            s.status = SectionStatus.COMPLETED
            s.response_text = f"Content {i}"
            sections.append(s)

        mock_session.query.return_value.filter.return_value.first.return_value = mock_expansion
        mock_session.query.return_value.filter.return_value.order_by.return_value.all.return_value = sections

        result = combine_sections(expansion_id=1, session=mock_session)

        # Verify order is preserved
        pos1 = result.find("## Section 1")
        pos2 = result.find("## Section 2")
        pos3 = result.find("## Section 3")
        pos4 = result.find("## Section 4")
        pos5 = result.find("## Section 5")

        assert pos1 < pos2 < pos3 < pos4 < pos5
