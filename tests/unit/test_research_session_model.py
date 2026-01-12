"""
Unit tests for ResearchSession model.
"""

from datetime import datetime
import pytest
from src.vulcanlab.data.models.research_session import ResearchSession
from src.vulcanlab.data.models.enums import SessionType, SessionStatus, ResearchPhase


class TestResearchSessionModel:
    """Tests for the ResearchSession model."""

    def test_create_research_session(self):
        """Test creating a research session with all required fields."""
        session = ResearchSession(
            collection_id=1,
            session_type=SessionType.MANUAL,
            thread_id="thread_123",
            current_phase=ResearchPhase.PLANNING,
            research_plan={"topic": "AI research", "steps": ["step1", "step2"]},
            state_data={"current_step": 1},
            status=SessionStatus.IN_PROGRESS
        )

        assert session.collection_id == 1
        assert session.session_type == SessionType.MANUAL
        assert session.thread_id == "thread_123"
        assert session.current_phase == ResearchPhase.PLANNING
        assert session.research_plan == {"topic": "AI research", "steps": ["step1", "step2"]}
        assert session.state_data == {"current_step": 1}
        assert session.status == SessionStatus.IN_PROGRESS

    def test_research_session_with_automated_type(self):
        """Test creating an automated research session."""
        session = ResearchSession(
            collection_id=2,
            session_type=SessionType.AUTOMATED,
            thread_id="thread_456",
            status=SessionStatus.IN_PROGRESS
        )

        assert session.session_type == SessionType.AUTOMATED
        assert session.collection_id == 2

    def test_research_session_enum_fields(self):
        """Test that enum fields accept valid enum values."""
        session = ResearchSession(
            collection_id=1,
            session_type=SessionType.MANUAL,
            thread_id="thread_789",
            current_phase=ResearchPhase.RESEARCH,
            status=SessionStatus.COMPLETED
        )

        assert session.session_type == SessionType.MANUAL
        assert session.current_phase == ResearchPhase.RESEARCH
        assert session.status == SessionStatus.COMPLETED

    def test_research_session_jsonb_fields(self):
        """Test that JSONB columns serialize and deserialize dictionaries correctly."""
        research_plan = {
            "objective": "Investigate climate change",
            "methodology": ["literature review", "data analysis"],
            "expected_outcomes": "Comprehensive report"
        }
        state_data = {
            "phase": "research",
            "progress": 0.5,
            "notes": ["note1", "note2"]
        }

        session = ResearchSession(
            collection_id=1,
            session_type=SessionType.MANUAL,
            thread_id="thread_jsonb",
            research_plan=research_plan,
            state_data=state_data,
            status=SessionStatus.IN_PROGRESS
        )

        assert session.research_plan == research_plan
        assert session.state_data == state_data
        assert session.research_plan["objective"] == "Investigate climate change"
        assert session.state_data["progress"] == 0.5

    def test_research_session_optional_fields(self):
        """Test creating a session with only required fields."""
        session = ResearchSession(
            collection_id=1,
            session_type=SessionType.MANUAL,
            thread_id="thread_minimal",
            status=SessionStatus.IN_PROGRESS
        )

        assert session.current_phase is None
        assert session.research_plan is None
        assert session.state_data is None
        assert session.completed_at is None

    def test_research_session_repr(self):
        """Test the string representation of a ResearchSession."""
        session = ResearchSession(
            id=1,
            collection_id=1,
            session_type=SessionType.MANUAL,
            thread_id="thread_repr",
            status=SessionStatus.COMPLETED
        )
        assert repr(session) == "<ResearchSession(id=1, thread_id='thread_repr', status='completed')>"

    def test_research_session_tablename(self):
        """Test the table name."""
        assert ResearchSession.__tablename__ == "research_sessions"

    def test_research_session_all_phases(self):
        """Test all research phases can be assigned."""
        phases = [
            ResearchPhase.PLANNING,
            ResearchPhase.RESEARCH,
            ResearchPhase.SYNTHESIS,
            ResearchPhase.EVALUATION,
            ResearchPhase.COMPLETED
        ]

        for phase in phases:
            session = ResearchSession(
                collection_id=1,
                session_type=SessionType.MANUAL,
                thread_id=f"thread_{phase.value}",
                current_phase=phase,
                status=SessionStatus.IN_PROGRESS
            )
            assert session.current_phase == phase

    def test_research_session_all_statuses(self):
        """Test all session statuses can be assigned."""
        statuses = [
            SessionStatus.IN_PROGRESS,
            SessionStatus.COMPLETED,
            SessionStatus.FAILED,
            SessionStatus.PAUSED
        ]

        for status in statuses:
            session = ResearchSession(
                collection_id=1,
                session_type=SessionType.MANUAL,
                thread_id=f"thread_{status.value}",
                status=status
            )
            assert session.status == status
