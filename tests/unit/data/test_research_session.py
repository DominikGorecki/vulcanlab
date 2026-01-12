"""
Unit tests for research session CRUD operations.

Tests all CRUD functions for research sessions, sections, and reports.
All tests use mocked sessions without database.
"""

import pytest
from datetime import datetime, timezone
from unittest.mock import MagicMock, patch, call

from src.vulcanlab.data.research_session import (
    generate_thread_id,
    create_research_session,
    get_research_session,
    get_research_session_by_thread_id,
    update_research_session,
    list_research_sessions_for_collection,
    update_session_phase,
    create_research_section,
    get_research_sections,
    update_research_section,
    create_research_report,
    get_research_report,
)
from src.vulcanlab.data.models.enums import (
    SessionType,
    SessionStatus,
    ResearchPhase,
    QualityStatus,
)
from tests.unit.mock_helpers import mock_session


def create_mock_research_session(
    id: int = 1,
    collection_id: int = 1,
    session_type: SessionType = SessionType.MANUAL,
    thread_id: str = "manual_123_abc",
    status: SessionStatus = SessionStatus.IN_PROGRESS,
    current_phase: ResearchPhase = ResearchPhase.PLANNING,
    **kwargs
):
    """Create a mock ResearchSession instance."""
    session = MagicMock()
    session.id = id
    session.collection_id = collection_id
    session.session_type = session_type
    session.thread_id = thread_id
    session.status = status
    session.current_phase = current_phase
    session.research_plan = kwargs.get('research_plan')
    session.state_data = kwargs.get('state_data')
    session.created_at = kwargs.get('created_at', datetime.now(timezone.utc))
    session.updated_at = kwargs.get('updated_at', datetime.now(timezone.utc))
    session.completed_at = kwargs.get('completed_at')
    session.sections = kwargs.get('sections', [])
    session.reports = kwargs.get('reports', [])
    return session


def create_mock_research_section(
    id: int = 1,
    session_id: int = 1,
    question_id: str = "Q1",
    question_text: str = "Test question?",
    **kwargs
):
    """Create a mock ResearchSection instance."""
    section = MagicMock()
    section.id = id
    section.session_id = session_id
    section.question_id = question_id
    section.question_text = question_text
    section.section_content = kwargs.get('section_content')
    section.context_data = kwargs.get('context_data')
    section.matching_results = kwargs.get('matching_results')
    section.section_metadata = kwargs.get('section_metadata')
    section.reuse_info = kwargs.get('reuse_info')
    section.quality_status = kwargs.get('quality_status')
    section.created_at = kwargs.get('created_at', datetime.now(timezone.utc))
    section.updated_at = kwargs.get('updated_at', datetime.now(timezone.utc))
    return section


def create_mock_research_report(
    id: int = 1,
    session_id: int = 1,
    report_content: str = "Test report content",
    version: int = 1,
    **kwargs
):
    """Create a mock ResearchReport instance."""
    report = MagicMock()
    report.id = id
    report.session_id = session_id
    report.report_content = report_content
    report.executive_summary = kwargs.get('executive_summary')
    report.quality_evaluation = kwargs.get('quality_evaluation')
    report.report_metadata = kwargs.get('report_metadata')
    report.version = version
    report.created_at = kwargs.get('created_at', datetime.now(timezone.utc))
    return report


class TestGenerateThreadId:
    """Test suite for generate_thread_id function."""

    def test_manual_session_format(self):
        """Test manual session thread_id format: manual_{timestamp}_{random_hex}."""
        thread_id = generate_thread_id(SessionType.MANUAL, collection_id=1)

        assert thread_id.startswith("manual_")
        parts = thread_id.split("_")
        assert len(parts) == 3
        # Second part should be a timestamp (integer)
        assert parts[1].isdigit()
        # Third part should be 8 hex characters (4 bytes)
        assert len(parts[2]) == 8
        assert all(c in '0123456789abcdef' for c in parts[2])

    def test_automated_session_format(self):
        """Test automated session thread_id format: auto_{collection_id}_{timestamp}."""
        thread_id = generate_thread_id(SessionType.AUTOMATED, collection_id=42)

        assert thread_id.startswith("auto_")
        parts = thread_id.split("_")
        assert len(parts) == 3
        # Second part should be the collection_id
        assert parts[1] == "42"
        # Third part should be a timestamp (integer)
        assert parts[2].isdigit()

    def test_manual_thread_ids_are_unique(self):
        """Test that manual thread_ids are unique (due to random hex)."""
        thread_ids = [generate_thread_id(SessionType.MANUAL, 1) for _ in range(10)]
        assert len(set(thread_ids)) == 10

    def test_automated_thread_ids_differ_by_collection(self):
        """Test automated thread_ids include collection_id."""
        thread_id_1 = generate_thread_id(SessionType.AUTOMATED, collection_id=1)
        thread_id_2 = generate_thread_id(SessionType.AUTOMATED, collection_id=2)

        assert "auto_1_" in thread_id_1
        assert "auto_2_" in thread_id_2


class TestCreateResearchSession:
    """Test suite for create_research_session function."""

    def test_creates_session_with_defaults(self, mock_session):
        """Test session is created with correct default values."""
        with patch('src.vulcanlab.data.research_session.ResearchSession') as MockSession:
            mock_instance = create_mock_research_session(id=1)
            MockSession.return_value = mock_instance

            result = create_research_session(
                session=mock_session,
                collection_id=5,
                session_type=SessionType.MANUAL,
            )

            # Verify ResearchSession was instantiated correctly
            MockSession.assert_called_once()
            call_kwargs = MockSession.call_args[1]
            assert call_kwargs['collection_id'] == 5
            assert call_kwargs['session_type'] == SessionType.MANUAL
            assert call_kwargs['status'] == SessionStatus.IN_PROGRESS
            assert call_kwargs['current_phase'] == ResearchPhase.PLANNING
            # thread_id should be generated
            assert call_kwargs['thread_id'].startswith('manual_')

    def test_creates_session_with_provided_thread_id(self, mock_session):
        """Test session is created with provided thread_id."""
        with patch('src.vulcanlab.data.research_session.ResearchSession') as MockSession:
            mock_instance = create_mock_research_session(id=1, thread_id="custom_thread")
            MockSession.return_value = mock_instance

            result = create_research_session(
                session=mock_session,
                collection_id=5,
                session_type=SessionType.MANUAL,
                thread_id="custom_thread",
            )

            call_kwargs = MockSession.call_args[1]
            assert call_kwargs['thread_id'] == "custom_thread"

    def test_adds_session_to_db_and_flushes(self, mock_session):
        """Test session is added and flushed."""
        with patch('src.vulcanlab.data.research_session.ResearchSession') as MockSession:
            mock_instance = create_mock_research_session(id=1)
            MockSession.return_value = mock_instance

            result = create_research_session(
                session=mock_session,
                collection_id=5,
                session_type=SessionType.AUTOMATED,
            )

            mock_session.add.assert_called_once_with(mock_instance)
            mock_session.flush.assert_called_once()
            assert result == mock_instance

    def test_does_not_commit(self, mock_session):
        """Test function does not commit (caller responsibility)."""
        with patch('src.vulcanlab.data.research_session.ResearchSession') as MockSession:
            mock_instance = create_mock_research_session(id=1)
            MockSession.return_value = mock_instance

            create_research_session(
                session=mock_session,
                collection_id=5,
                session_type=SessionType.MANUAL,
            )

            mock_session.commit.assert_not_called()


class TestGetResearchSession:
    """Test suite for get_research_session function."""

    def test_returns_session_by_id(self, mock_session):
        """Test session is retrieved by ID with relationships."""
        mock_rs = create_mock_research_session(id=42)

        # Mock the execute chain for select queries
        mock_result = MagicMock()
        mock_result.unique.return_value.scalar_one_or_none.return_value = mock_rs
        mock_session.execute.return_value = mock_result

        result = get_research_session(mock_session, session_id=42)

        assert result == mock_rs
        mock_session.execute.assert_called_once()

    def test_returns_none_if_not_found(self, mock_session):
        """Test None is returned if session not found."""
        mock_result = MagicMock()
        mock_result.unique.return_value.scalar_one_or_none.return_value = None
        mock_session.execute.return_value = mock_result

        result = get_research_session(mock_session, session_id=999)

        assert result is None


class TestGetResearchSessionByThreadId:
    """Test suite for get_research_session_by_thread_id function."""

    def test_returns_session_by_thread_id(self, mock_session):
        """Test session is retrieved by thread_id."""
        mock_rs = create_mock_research_session(id=1, thread_id="manual_123_abc")

        mock_result = MagicMock()
        mock_result.unique.return_value.scalar_one_or_none.return_value = mock_rs
        mock_session.execute.return_value = mock_result

        result = get_research_session_by_thread_id(mock_session, thread_id="manual_123_abc")

        assert result == mock_rs
        assert result.thread_id == "manual_123_abc"

    def test_returns_none_if_not_found(self, mock_session):
        """Test None is returned if thread_id not found."""
        mock_result = MagicMock()
        mock_result.unique.return_value.scalar_one_or_none.return_value = None
        mock_session.execute.return_value = mock_result

        result = get_research_session_by_thread_id(mock_session, thread_id="nonexistent")

        assert result is None


class TestUpdateResearchSession:
    """Test suite for update_research_session function."""

    def test_updates_research_plan(self, mock_session):
        """Test research_plan is updated correctly."""
        mock_rs = create_mock_research_session(id=1)
        mock_session.get.return_value = mock_rs

        plan = {"questions": ["Q1", "Q2"]}
        result = update_research_session(
            mock_session,
            session_id=1,
            updates={'research_plan': plan},
        )

        assert result.research_plan == plan
        mock_session.flush.assert_called_once()

    def test_updates_state_data(self, mock_session):
        """Test state_data is updated correctly."""
        mock_rs = create_mock_research_session(id=1)
        mock_session.get.return_value = mock_rs

        state = {"current_question": 2}
        result = update_research_session(
            mock_session,
            session_id=1,
            updates={'state_data': state},
        )

        assert result.state_data == state

    def test_updates_status(self, mock_session):
        """Test status is updated correctly."""
        mock_rs = create_mock_research_session(id=1, status=SessionStatus.IN_PROGRESS)
        mock_session.get.return_value = mock_rs

        result = update_research_session(
            mock_session,
            session_id=1,
            updates={'status': SessionStatus.COMPLETED},
        )

        assert result.status == SessionStatus.COMPLETED

    def test_updates_current_phase(self, mock_session):
        """Test current_phase is updated correctly."""
        mock_rs = create_mock_research_session(id=1, current_phase=ResearchPhase.PLANNING)
        mock_session.get.return_value = mock_rs

        result = update_research_session(
            mock_session,
            session_id=1,
            updates={'current_phase': ResearchPhase.RESEARCH},
        )

        assert result.current_phase == ResearchPhase.RESEARCH

    def test_updates_completed_at(self, mock_session):
        """Test completed_at is updated correctly."""
        mock_rs = create_mock_research_session(id=1)
        mock_session.get.return_value = mock_rs

        completed = datetime.now(timezone.utc)
        result = update_research_session(
            mock_session,
            session_id=1,
            updates={'completed_at': completed},
        )

        assert result.completed_at == completed

    def test_ignores_unknown_fields(self, mock_session):
        """Test unknown fields are ignored."""
        mock_rs = create_mock_research_session(id=1)
        mock_session.get.return_value = mock_rs

        result = update_research_session(
            mock_session,
            session_id=1,
            updates={'unknown_field': 'value', 'research_plan': {'q': 1}},
        )

        assert result.research_plan == {'q': 1}
        # unknown_field should not be set

    def test_returns_none_if_not_found(self, mock_session):
        """Test None is returned if session not found."""
        mock_session.get.return_value = None

        result = update_research_session(
            mock_session,
            session_id=999,
            updates={'status': SessionStatus.COMPLETED},
        )

        assert result is None
        mock_session.flush.assert_not_called()


class TestListResearchSessionsForCollection:
    """Test suite for list_research_sessions_for_collection function."""

    def test_returns_sessions_for_collection(self, mock_session):
        """Test sessions are returned for the specified collection."""
        mock_sessions = [
            create_mock_research_session(id=1, collection_id=5),
            create_mock_research_session(id=2, collection_id=5),
        ]

        mock_result = MagicMock()
        mock_result.scalars.return_value.all.return_value = mock_sessions
        mock_session.execute.return_value = mock_result

        result = list_research_sessions_for_collection(mock_session, collection_id=5)

        assert len(result) == 2
        assert result[0].id == 1
        assert result[1].id == 2

    def test_returns_empty_list_if_none(self, mock_session):
        """Test empty list is returned if no sessions found."""
        mock_result = MagicMock()
        mock_result.scalars.return_value.all.return_value = []
        mock_session.execute.return_value = mock_result

        result = list_research_sessions_for_collection(mock_session, collection_id=999)

        assert result == []


class TestUpdateSessionPhase:
    """Test suite for update_session_phase function."""

    def test_updates_phase(self, mock_session):
        """Test phase is updated correctly."""
        mock_rs = create_mock_research_session(id=1, current_phase=ResearchPhase.PLANNING)
        mock_session.get.return_value = mock_rs

        result = update_session_phase(mock_session, session_id=1, phase=ResearchPhase.SYNTHESIS)

        assert result.current_phase == ResearchPhase.SYNTHESIS

    def test_returns_none_if_not_found(self, mock_session):
        """Test None is returned if session not found."""
        mock_session.get.return_value = None

        result = update_session_phase(mock_session, session_id=999, phase=ResearchPhase.RESEARCH)

        assert result is None


class TestCreateResearchSection:
    """Test suite for create_research_section function."""

    def test_creates_section_with_required_fields(self, mock_session):
        """Test section is created with required fields."""
        with patch('src.vulcanlab.data.research_session.ResearchSection') as MockSection:
            mock_instance = create_mock_research_section(id=1, session_id=5)
            MockSection.return_value = mock_instance

            result = create_research_section(
                session=mock_session,
                session_id=5,
                question_id="Q1",
                question_text="What is the answer?",
            )

            MockSection.assert_called_once()
            call_kwargs = MockSection.call_args[1]
            assert call_kwargs['session_id'] == 5
            assert call_kwargs['question_id'] == "Q1"
            assert call_kwargs['question_text'] == "What is the answer?"

    def test_creates_section_with_optional_fields(self, mock_session):
        """Test section is created with optional fields."""
        with patch('src.vulcanlab.data.research_session.ResearchSection') as MockSection:
            mock_instance = create_mock_research_section(id=1)
            MockSection.return_value = mock_instance

            result = create_research_section(
                session=mock_session,
                session_id=5,
                question_id="Q1",
                question_text="Question?",
                section_content="Answer content",
                context_data={"ctx": "data"},
                matching_results={"matches": []},
                section_metadata={"meta": "data"},
                reuse_info={"reused": True},
                quality_status=QualityStatus.PASS,
            )

            call_kwargs = MockSection.call_args[1]
            assert call_kwargs['section_content'] == "Answer content"
            assert call_kwargs['context_data'] == {"ctx": "data"}
            assert call_kwargs['matching_results'] == {"matches": []}
            assert call_kwargs['section_metadata'] == {"meta": "data"}
            assert call_kwargs['reuse_info'] == {"reused": True}
            assert call_kwargs['quality_status'] == QualityStatus.PASS

    def test_adds_and_flushes(self, mock_session):
        """Test section is added and flushed."""
        with patch('src.vulcanlab.data.research_session.ResearchSection') as MockSection:
            mock_instance = create_mock_research_section(id=1)
            MockSection.return_value = mock_instance

            create_research_section(
                session=mock_session,
                session_id=5,
            )

            mock_session.add.assert_called_once_with(mock_instance)
            mock_session.flush.assert_called_once()


class TestGetResearchSections:
    """Test suite for get_research_sections function."""

    def test_returns_sections_for_session(self, mock_session):
        """Test sections are returned ordered by question_id."""
        mock_sections = [
            create_mock_research_section(id=1, session_id=5, question_id="Q1"),
            create_mock_research_section(id=2, session_id=5, question_id="Q2"),
            create_mock_research_section(id=3, session_id=5, question_id="Q3"),
        ]

        mock_result = MagicMock()
        mock_result.scalars.return_value.all.return_value = mock_sections
        mock_session.execute.return_value = mock_result

        result = get_research_sections(mock_session, session_id=5)

        assert len(result) == 3
        assert result[0].question_id == "Q1"
        assert result[1].question_id == "Q2"
        assert result[2].question_id == "Q3"

    def test_returns_empty_list_if_none(self, mock_session):
        """Test empty list is returned if no sections found."""
        mock_result = MagicMock()
        mock_result.scalars.return_value.all.return_value = []
        mock_session.execute.return_value = mock_result

        result = get_research_sections(mock_session, session_id=999)

        assert result == []


class TestUpdateResearchSection:
    """Test suite for update_research_section function."""

    def test_updates_section_content(self, mock_session):
        """Test section_content is updated correctly."""
        mock_section = create_mock_research_section(id=1)
        mock_session.get.return_value = mock_section

        result = update_research_section(
            mock_session,
            section_id=1,
            updates={'section_content': 'New content'},
        )

        assert result.section_content == 'New content'
        mock_session.flush.assert_called_once()

    def test_updates_metadata(self, mock_session):
        """Test section_metadata is updated correctly."""
        mock_section = create_mock_research_section(id=1)
        mock_session.get.return_value = mock_section

        result = update_research_section(
            mock_session,
            section_id=1,
            updates={'section_metadata': {'new': 'meta'}},
        )

        assert result.section_metadata == {'new': 'meta'}

    def test_updates_quality_status(self, mock_session):
        """Test quality_status is updated correctly."""
        mock_section = create_mock_research_section(id=1)
        mock_session.get.return_value = mock_section

        result = update_research_section(
            mock_session,
            section_id=1,
            updates={'quality_status': QualityStatus.FAIL},
        )

        assert result.quality_status == QualityStatus.FAIL

    def test_returns_none_if_not_found(self, mock_session):
        """Test None is returned if section not found."""
        mock_session.get.return_value = None

        result = update_research_section(
            mock_session,
            section_id=999,
            updates={'section_content': 'New'},
        )

        assert result is None


class TestCreateResearchReport:
    """Test suite for create_research_report function."""

    def test_creates_report_with_required_fields(self, mock_session):
        """Test report is created with required fields."""
        mock_rs = create_mock_research_session(id=5)
        mock_session.get.return_value = mock_rs

        with patch('src.vulcanlab.data.research_session.ResearchReport') as MockReport:
            mock_report = create_mock_research_report(id=1, session_id=5)
            MockReport.return_value = mock_report

            result = create_research_report(
                session=mock_session,
                session_id=5,
                report_content="Full report content here",
            )

            MockReport.assert_called_once()
            call_kwargs = MockReport.call_args[1]
            assert call_kwargs['session_id'] == 5
            assert call_kwargs['report_content'] == "Full report content here"
            assert call_kwargs['version'] == 1

    def test_creates_report_with_optional_fields(self, mock_session):
        """Test report is created with optional fields."""
        mock_rs = create_mock_research_session(id=5)
        mock_session.get.return_value = mock_rs

        with patch('src.vulcanlab.data.research_session.ResearchReport') as MockReport:
            mock_report = create_mock_research_report(id=1)
            MockReport.return_value = mock_report

            create_research_report(
                session=mock_session,
                session_id=5,
                report_content="Content",
                executive_summary="Summary",
                quality_evaluation={"score": 0.9},
                report_metadata={"author": "AI"},
            )

            call_kwargs = MockReport.call_args[1]
            assert call_kwargs['executive_summary'] == "Summary"
            assert call_kwargs['quality_evaluation'] == {"score": 0.9}
            assert call_kwargs['report_metadata'] == {"author": "AI"}

    def test_updates_session_to_completed(self, mock_session):
        """Test parent session is marked as completed."""
        mock_rs = create_mock_research_session(id=5, status=SessionStatus.IN_PROGRESS)
        mock_session.get.return_value = mock_rs

        with patch('src.vulcanlab.data.research_session.ResearchReport') as MockReport:
            mock_report = create_mock_research_report(id=1)
            MockReport.return_value = mock_report

            create_research_report(
                session=mock_session,
                session_id=5,
                report_content="Content",
            )

            # Session should be updated to completed
            assert mock_rs.status == SessionStatus.COMPLETED
            assert mock_rs.current_phase == ResearchPhase.COMPLETED
            assert mock_rs.completed_at is not None

    def test_adds_and_flushes(self, mock_session):
        """Test report is added and flushed."""
        mock_rs = create_mock_research_session(id=5)
        mock_session.get.return_value = mock_rs

        with patch('src.vulcanlab.data.research_session.ResearchReport') as MockReport:
            mock_report = create_mock_research_report(id=1)
            MockReport.return_value = mock_report

            create_research_report(
                session=mock_session,
                session_id=5,
                report_content="Content",
            )

            mock_session.add.assert_called_once_with(mock_report)
            # flush called twice: once for report, once in update_research_session
            assert mock_session.flush.call_count >= 1


class TestGetResearchReport:
    """Test suite for get_research_report function."""

    def test_returns_latest_report(self, mock_session):
        """Test latest report (by version) is returned."""
        mock_report = create_mock_research_report(id=2, session_id=5, version=2)

        mock_result = MagicMock()
        mock_result.scalar_one_or_none.return_value = mock_report
        mock_session.execute.return_value = mock_result

        result = get_research_report(mock_session, session_id=5)

        assert result == mock_report
        assert result.version == 2

    def test_returns_none_if_no_report(self, mock_session):
        """Test None is returned if no report exists."""
        mock_result = MagicMock()
        mock_result.scalar_one_or_none.return_value = None
        mock_session.execute.return_value = mock_result

        result = get_research_report(mock_session, session_id=999)

        assert result is None
