"""
Unit tests for AnswerExpansion and ExpansionSection models.

Tests model creation, field validation, enum values, and basic logic.
Database-specific tests (CASCADE, constraints, timestamps) should be in integration tests.

Usage:
    pytest tests/unit/test_expansion_models.py -v
"""

import pytest
from datetime import datetime
from unittest.mock import MagicMock, patch

from vulcanlab.data.models.expansion import (
    AnswerExpansion,
    ExpansionSection,
    ExpansionMode,
    ExpansionStatus,
    SectionStatus,
)


class TestExpansionModeEnum:
    """Tests for ExpansionMode enum."""

    def test_automatic_value(self):
        """Test AUTOMATIC enum value is lowercase."""
        assert ExpansionMode.AUTOMATIC == 'automatic'
        assert ExpansionMode.AUTOMATIC.value == 'automatic'

    def test_manual_value(self):
        """Test MANUAL enum value is lowercase."""
        assert ExpansionMode.MANUAL == 'manual'
        assert ExpansionMode.MANUAL.value == 'manual'

    def test_all_modes(self):
        """Test all ExpansionMode values."""
        modes = list(ExpansionMode)
        assert ExpansionMode.AUTOMATIC in modes
        assert ExpansionMode.MANUAL in modes
        assert len(modes) == 2


class TestExpansionStatusEnum:
    """Tests for ExpansionStatus enum."""

    def test_created_value(self):
        """Test CREATED enum value is lowercase."""
        assert ExpansionStatus.CREATED == 'created'
        assert ExpansionStatus.CREATED.value == 'created'

    def test_breakdown_pending_value(self):
        """Test BREAKDOWN_PENDING enum value is lowercase."""
        assert ExpansionStatus.BREAKDOWN_PENDING == 'breakdown_pending'
        assert ExpansionStatus.BREAKDOWN_PENDING.value == 'breakdown_pending'

    def test_breakdown_complete_value(self):
        """Test BREAKDOWN_COMPLETE enum value is lowercase."""
        assert ExpansionStatus.BREAKDOWN_COMPLETE == 'breakdown_complete'
        assert ExpansionStatus.BREAKDOWN_COMPLETE.value == 'breakdown_complete'

    def test_sections_in_progress_value(self):
        """Test SECTIONS_IN_PROGRESS enum value is lowercase."""
        assert ExpansionStatus.SECTIONS_IN_PROGRESS == 'sections_in_progress'
        assert ExpansionStatus.SECTIONS_IN_PROGRESS.value == 'sections_in_progress'

    def test_combining_value(self):
        """Test COMBINING enum value is lowercase."""
        assert ExpansionStatus.COMBINING == 'combining'
        assert ExpansionStatus.COMBINING.value == 'combining'

    def test_completed_value(self):
        """Test COMPLETED enum value is lowercase."""
        assert ExpansionStatus.COMPLETED == 'completed'
        assert ExpansionStatus.COMPLETED.value == 'completed'

    def test_failed_value(self):
        """Test FAILED enum value is lowercase."""
        assert ExpansionStatus.FAILED == 'failed'
        assert ExpansionStatus.FAILED.value == 'failed'

    def test_all_statuses(self):
        """Test all ExpansionStatus values match spec."""
        statuses = list(ExpansionStatus)
        expected = [
            'created', 'breakdown_pending', 'breakdown_complete',
            'sections_in_progress', 'combining', 'completed', 'failed'
        ]
        assert len(statuses) == 7
        for status in statuses:
            assert status.value in expected


class TestSectionStatusEnum:
    """Tests for SectionStatus enum."""

    def test_pending_value(self):
        """Test PENDING enum value is lowercase."""
        assert SectionStatus.PENDING == 'pending'
        assert SectionStatus.PENDING.value == 'pending'

    def test_expanding_value(self):
        """Test EXPANDING enum value is lowercase."""
        assert SectionStatus.EXPANDING == 'expanding'
        assert SectionStatus.EXPANDING.value == 'expanding'

    def test_ready_value(self):
        """Test READY enum value is lowercase."""
        assert SectionStatus.READY == 'ready'
        assert SectionStatus.READY.value == 'ready'

    def test_generating_value(self):
        """Test GENERATING enum value is lowercase."""
        assert SectionStatus.GENERATING == 'generating'
        assert SectionStatus.GENERATING.value == 'generating'

    def test_completed_value(self):
        """Test COMPLETED enum value is lowercase."""
        assert SectionStatus.COMPLETED == 'completed'
        assert SectionStatus.COMPLETED.value == 'completed'

    def test_failed_value(self):
        """Test FAILED enum value is lowercase."""
        assert SectionStatus.FAILED == 'failed'
        assert SectionStatus.FAILED.value == 'failed'

    def test_all_statuses(self):
        """Test all SectionStatus values match spec."""
        statuses = list(SectionStatus)
        expected = ['pending', 'expanding', 'ready', 'generating', 'completed', 'failed']
        assert len(statuses) == 6
        for status in statuses:
            assert status.value in expected


class TestAnswerExpansionCreation:
    """Test basic model creation and field values for AnswerExpansion."""

    def test_create_answer_expansion(self):
        """Test creating an AnswerExpansion instance."""
        expansion = AnswerExpansion(
            result_id=1,
            query_id=1,
            mode=ExpansionMode.AUTOMATIC,
            status=ExpansionStatus.CREATED
        )

        assert expansion.result_id == 1
        assert expansion.query_id == 1
        assert expansion.mode == ExpansionMode.AUTOMATIC
        assert expansion.status == ExpansionStatus.CREATED

    def test_create_expansion_with_manual_mode(self):
        """Test creating an expansion in manual mode."""
        expansion = AnswerExpansion(
            result_id=2,
            query_id=2,
            mode=ExpansionMode.MANUAL,
            status=ExpansionStatus.CREATED
        )

        assert expansion.mode == ExpansionMode.MANUAL

    def test_create_expansion_with_combined_report(self):
        """Test creating an expansion with combined report."""
        report = "# Combined Report\n\n## Section 1\nContent..."
        expansion = AnswerExpansion(
            result_id=1,
            query_id=1,
            mode=ExpansionMode.AUTOMATIC,
            status=ExpansionStatus.COMPLETED,
            combined_report=report
        )

        assert expansion.combined_report == report

    def test_create_expansion_with_metadata(self):
        """Test creating an expansion with expansion_metadata."""
        expansion_metadata = {"source_tokens": 5000, "breakdown_model": "gpt-4"}
        expansion = AnswerExpansion(
            result_id=1,
            query_id=1,
            mode=ExpansionMode.AUTOMATIC,
            status=ExpansionStatus.CREATED,
            expansion_metadata=expansion_metadata
        )

        assert expansion.expansion_metadata == expansion_metadata

    def test_repr(self):
        """Test __repr__ method."""
        expansion = AnswerExpansion(
            result_id=1,
            query_id=1,
            mode=ExpansionMode.AUTOMATIC,
            status=ExpansionStatus.CREATED
        )
        expansion.id = 1

        repr_str = repr(expansion)
        assert "AnswerExpansion" in repr_str
        assert "1" in repr_str
        assert "created" in repr_str

    def test_tablename(self):
        """Test that AnswerExpansion uses correct table name."""
        assert AnswerExpansion.__tablename__ == "answer_expansions"


class TestExpansionSectionCreation:
    """Test basic model creation and field values for ExpansionSection."""

    def test_create_expansion_section(self):
        """Test creating an ExpansionSection instance."""
        section = ExpansionSection(
            expansion_id=1,
            order=1,
            heading="Introduction to Topic",
            summary="Brief overview of the main concepts",
            expansion_prompt="Explain the introduction to the topic in detail",
            status=SectionStatus.PENDING
        )

        assert section.expansion_id == 1
        assert section.order == 1
        assert section.heading == "Introduction to Topic"
        assert section.summary == "Brief overview of the main concepts"
        assert section.expansion_prompt == "Explain the introduction to the topic in detail"
        assert section.status == SectionStatus.PENDING

    def test_create_section_with_rag_data(self):
        """Test creating a section with RAG pipeline data."""
        section = ExpansionSection(
            expansion_id=1,
            order=2,
            heading="Technical Details",
            summary="Deep dive into technical aspects",
            expansion_prompt="Explain the technical details",
            status=SectionStatus.READY,
            expanded_queries=["query 1", "query 2"],
            hyde_answer="Hypothetical answer text",
            intent="informational",
            entities=["entity1", "entity2"],
            retrieved_context=[{"chunk_id": 1, "content": "..."}],
            clean_retrieval_context=[{"chunk_id": 1, "content": "cleaned..."}],
            augmented_prompt="Full augmented prompt with context"
        )

        assert section.expanded_queries == ["query 1", "query 2"]
        assert section.hyde_answer == "Hypothetical answer text"
        assert section.intent == "informational"
        assert section.entities == ["entity1", "entity2"]
        assert len(section.retrieved_context) == 1
        assert len(section.clean_retrieval_context) == 1
        assert section.augmented_prompt == "Full augmented prompt with context"

    def test_create_section_with_response(self):
        """Test creating a completed section with response."""
        section = ExpansionSection(
            expansion_id=1,
            order=1,
            heading="Section Title",
            summary="Section summary",
            expansion_prompt="Expansion prompt",
            status=SectionStatus.COMPLETED,
            response_text="This is the generated response for the section."
        )

        assert section.status == SectionStatus.COMPLETED
        assert section.response_text == "This is the generated response for the section."

    def test_create_failed_section(self):
        """Test creating a failed section with error message."""
        section = ExpansionSection(
            expansion_id=1,
            order=3,
            heading="Failed Section",
            summary="This section failed",
            expansion_prompt="Prompt that failed",
            status=SectionStatus.FAILED,
            error_message="LLM timeout after 30 seconds"
        )

        assert section.status == SectionStatus.FAILED
        assert section.error_message == "LLM timeout after 30 seconds"

    def test_repr(self):
        """Test __repr__ method."""
        section = ExpansionSection(
            expansion_id=1,
            order=2,
            heading="Test Section",
            summary="Summary",
            expansion_prompt="Prompt",
            status=SectionStatus.PENDING
        )
        section.id = 5

        repr_str = repr(section)
        assert "ExpansionSection" in repr_str
        assert "5" in repr_str
        assert "2" in repr_str  # order
        assert "pending" in repr_str

    def test_tablename(self):
        """Test that ExpansionSection uses correct table name."""
        assert ExpansionSection.__tablename__ == "expansion_sections"


class TestAnswerExpansionTimestamps:
    """Test timestamp fields for AnswerExpansion."""

    def test_timestamps_can_be_set(self):
        """Test that timestamps can be set explicitly."""
        now = datetime.now()
        expansion = AnswerExpansion(
            result_id=1,
            query_id=1,
            mode=ExpansionMode.AUTOMATIC,
            status=ExpansionStatus.CREATED,
            created_at=now,
            updated_at=now
        )

        assert expansion.created_at == now
        assert expansion.updated_at == now


class TestExpansionSectionTimestamps:
    """Test timestamp fields for ExpansionSection."""

    def test_timestamps_can_be_set(self):
        """Test that timestamps can be set explicitly."""
        now = datetime.now()
        section = ExpansionSection(
            expansion_id=1,
            order=1,
            heading="Test",
            summary="Summary",
            expansion_prompt="Prompt",
            status=SectionStatus.PENDING,
            created_at=now,
            updated_at=now
        )

        assert section.created_at == now
        assert section.updated_at == now


class TestAnswerExpansionCRUD:
    """Test CRUD operations with mocked database."""

    @patch('vulcanlab.data.database.get_session')
    def test_create_expansion(self, mock_get_session):
        """Test creating an AnswerExpansion."""
        mock_session = MagicMock()
        mock_get_session.return_value.__enter__.return_value = mock_session

        with mock_get_session() as session:
            expansion = AnswerExpansion(
                result_id=1,
                query_id=1,
                mode=ExpansionMode.AUTOMATIC,
                status=ExpansionStatus.CREATED
            )
            session.add(expansion)
            session.commit()

            session.add.assert_called_once()
            session.commit.assert_called_once()

    @patch('vulcanlab.data.database.get_session')
    def test_update_expansion_status(self, mock_get_session):
        """Test updating an expansion status."""
        mock_session = MagicMock()
        mock_get_session.return_value.__enter__.return_value = mock_session

        with mock_get_session() as session:
            expansion = AnswerExpansion(
                result_id=1,
                query_id=1,
                mode=ExpansionMode.AUTOMATIC,
                status=ExpansionStatus.CREATED
            )
            expansion.id = 1

            expansion.status = ExpansionStatus.BREAKDOWN_COMPLETE
            session.commit()

            assert expansion.status == ExpansionStatus.BREAKDOWN_COMPLETE
            session.commit.assert_called_once()


class TestExpansionSectionCRUD:
    """Test CRUD operations for ExpansionSection with mocked database."""

    @patch('vulcanlab.data.database.get_session')
    def test_create_section(self, mock_get_session):
        """Test creating an ExpansionSection."""
        mock_session = MagicMock()
        mock_get_session.return_value.__enter__.return_value = mock_session

        with mock_get_session() as session:
            section = ExpansionSection(
                expansion_id=1,
                order=1,
                heading="Test Section",
                summary="Summary",
                expansion_prompt="Prompt",
                status=SectionStatus.PENDING
            )
            session.add(section)
            session.commit()

            session.add.assert_called_once()
            session.commit.assert_called_once()

    @patch('vulcanlab.data.database.get_session')
    def test_update_section_status(self, mock_get_session):
        """Test updating a section status through the pipeline."""
        mock_session = MagicMock()
        mock_get_session.return_value.__enter__.return_value = mock_session

        with mock_get_session() as session:
            section = ExpansionSection(
                expansion_id=1,
                order=1,
                heading="Test",
                summary="Summary",
                expansion_prompt="Prompt",
                status=SectionStatus.PENDING
            )
            section.id = 1

            # Simulate status progression
            section.status = SectionStatus.EXPANDING
            assert section.status == SectionStatus.EXPANDING

            section.status = SectionStatus.READY
            assert section.status == SectionStatus.READY

            section.status = SectionStatus.GENERATING
            assert section.status == SectionStatus.GENERATING

            section.status = SectionStatus.COMPLETED
            section.response_text = "Generated response"
            session.commit()

            assert section.status == SectionStatus.COMPLETED
            assert section.response_text == "Generated response"


class TestRelationships:
    """Test relationships between models (without database)."""

    def test_expansion_has_result_id(self):
        """Test that AnswerExpansion has result_id attribute."""
        expansion = AnswerExpansion(
            result_id=5,
            query_id=3,
            mode=ExpansionMode.AUTOMATIC,
            status=ExpansionStatus.CREATED
        )

        assert expansion.result_id == 5
        assert expansion.query_id == 3

    def test_section_has_expansion_id(self):
        """Test that ExpansionSection has expansion_id attribute."""
        section = ExpansionSection(
            expansion_id=10,
            order=1,
            heading="Test",
            summary="Summary",
            expansion_prompt="Prompt",
            status=SectionStatus.PENDING
        )

        assert section.expansion_id == 10

    def test_multiple_sections_same_expansion(self):
        """Test that multiple sections can reference the same expansion_id."""
        expansion_id = 5

        section1 = ExpansionSection(
            expansion_id=expansion_id,
            order=1,
            heading="Section 1",
            summary="Summary 1",
            expansion_prompt="Prompt 1",
            status=SectionStatus.PENDING
        )
        section2 = ExpansionSection(
            expansion_id=expansion_id,
            order=2,
            heading="Section 2",
            summary="Summary 2",
            expansion_prompt="Prompt 2",
            status=SectionStatus.PENDING
        )
        section3 = ExpansionSection(
            expansion_id=expansion_id,
            order=3,
            heading="Section 3",
            summary="Summary 3",
            expansion_prompt="Prompt 3",
            status=SectionStatus.PENDING
        )

        assert section1.expansion_id == expansion_id
        assert section2.expansion_id == expansion_id
        assert section3.expansion_id == expansion_id
        assert section1.order < section2.order < section3.order
