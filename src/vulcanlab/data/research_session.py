"""
CRUD operations for research sessions, sections, and reports.
"""

import secrets
import time
from datetime import datetime, timezone
from typing import Dict, List, Optional, Any

from sqlalchemy import select
from sqlalchemy.orm import Session, joinedload

from .models.research_session import ResearchSession
from .models.research_section import ResearchSection
from .models.research_report import ResearchReport
from .models.enums import SessionType, SessionStatus, ResearchPhase, QualityStatus


def generate_thread_id(session_type: SessionType, collection_id: int) -> str:
    """
    Generate a unique thread_id for a research session.

    Args:
        session_type: Type of session (manual or automated).
        collection_id: ID of the collection.

    Returns:
        Thread ID string in format:
        - manual: "manual_{timestamp}_{random_hex}"
        - automated: "auto_{collection_id}_{timestamp}"
    """
    timestamp = int(time.time())
    if session_type == SessionType.MANUAL:
        random_hex = secrets.token_hex(4)
        return f"manual_{timestamp}_{random_hex}"
    else:
        return f"auto_{collection_id}_{timestamp}"


# --- ResearchSession CRUD ---


def create_research_session(
    session: Session,
    collection_id: int,
    session_type: SessionType,
    thread_id: Optional[str] = None,
) -> ResearchSession:
    """
    Create a new research session.

    Args:
        session: SQLAlchemy session (managed by caller).
        collection_id: ID of the collection this session belongs to.
        session_type: Type of session (manual or automated).
        thread_id: Optional thread ID. If None, one will be generated.

    Returns:
        The created ResearchSession object with ID populated.
    """
    if thread_id is None:
        thread_id = generate_thread_id(session_type, collection_id)

    research_session = ResearchSession(
        collection_id=collection_id,
        session_type=session_type,
        thread_id=thread_id,
        status=SessionStatus.IN_PROGRESS,
        current_phase=ResearchPhase.PLANNING,
    )
    session.add(research_session)
    session.flush()  # Get the ID without committing
    return research_session


def get_research_session(
    session: Session,
    session_id: int,
) -> Optional[ResearchSession]:
    """
    Get a research session by ID with related sections and reports.

    Args:
        session: SQLAlchemy session (managed by caller).
        session_id: ID of the research session.

    Returns:
        ResearchSession object or None if not found.
    """
    query = (
        select(ResearchSession)
        .options(
            joinedload(ResearchSession.sections),
            joinedload(ResearchSession.reports),
        )
        .where(ResearchSession.id == session_id)
    )
    result = session.execute(query).unique().scalar_one_or_none()
    return result


def get_research_session_by_thread_id(
    session: Session,
    thread_id: str,
) -> Optional[ResearchSession]:
    """
    Get a research session by thread_id (uses unique index).

    Args:
        session: SQLAlchemy session (managed by caller).
        thread_id: Unique thread identifier.

    Returns:
        ResearchSession object or None if not found.
    """
    query = (
        select(ResearchSession)
        .options(
            joinedload(ResearchSession.sections),
            joinedload(ResearchSession.reports),
        )
        .where(ResearchSession.thread_id == thread_id)
    )
    result = session.execute(query).unique().scalar_one_or_none()
    return result


def update_research_session(
    session: Session,
    session_id: int,
    updates: Dict[str, Any],
) -> Optional[ResearchSession]:
    """
    Update a research session.

    Args:
        session: SQLAlchemy session (managed by caller).
        session_id: ID of the research session to update.
        updates: Dictionary of fields to update. Supported keys:
            - current_phase: ResearchPhase enum value
            - research_plan: dict
            - state_data: dict
            - status: SessionStatus enum value
            - completed_at: datetime

    Returns:
        Updated ResearchSession object or None if not found.
    """
    research_session = session.get(ResearchSession, session_id)
    if not research_session:
        return None

    allowed_fields = {'current_phase', 'research_plan', 'state_data', 'status', 'completed_at'}
    for key, value in updates.items():
        if key in allowed_fields:
            setattr(research_session, key, value)

    session.flush()
    return research_session


def list_research_sessions_for_collection(
    session: Session,
    collection_id: int,
) -> List[ResearchSession]:
    """
    List all research sessions for a collection, ordered by created_at DESC.

    Args:
        session: SQLAlchemy session (managed by caller).
        collection_id: ID of the collection.

    Returns:
        List of ResearchSession objects.
    """
    query = (
        select(ResearchSession)
        .where(ResearchSession.collection_id == collection_id)
        .order_by(ResearchSession.created_at.desc())
    )
    result = session.execute(query).scalars().all()
    return list(result)


def update_session_phase(
    session: Session,
    session_id: int,
    phase: ResearchPhase,
) -> Optional[ResearchSession]:
    """
    Update the current_phase of a research session.

    Args:
        session: SQLAlchemy session (managed by caller).
        session_id: ID of the research session.
        phase: New ResearchPhase value.

    Returns:
        Updated ResearchSession object or None if not found.
    """
    return update_research_session(session, session_id, {'current_phase': phase})


# --- ResearchSection CRUD ---


def create_research_section(
    session: Session,
    session_id: int,
    question_id: Optional[str] = None,
    question_text: Optional[str] = None,
    section_content: Optional[str] = None,
    context_data: Optional[Dict[str, Any]] = None,
    matching_results: Optional[Dict[str, Any]] = None,
    section_metadata: Optional[Dict[str, Any]] = None,
    reuse_info: Optional[Dict[str, Any]] = None,
    quality_status: QualityStatus = QualityStatus.PENDING,
) -> ResearchSection:
    """
    Create a new research section for a session.

    Args:
        session: SQLAlchemy session (managed by caller).
        session_id: ID of the parent research session.
        question_id: Optional identifier for the question.
        question_text: Optional full question text.
        section_content: Optional research content for this section.
        context_data: Optional context information dict.
        matching_results: Optional matching results dict.
        section_metadata: Optional metadata dict.
        reuse_info: Optional content reuse information dict.
        quality_status: Quality assessment status (defaults to PENDING).

    Returns:
        The created ResearchSection object with ID populated.
    """
    research_section = ResearchSection(
        session_id=session_id,
        question_id=question_id,
        question_text=question_text,
        section_content=section_content,
        context_data=context_data,
        matching_results=matching_results,
        section_metadata=section_metadata,
        reuse_info=reuse_info,
        quality_status=quality_status,
    )
    session.add(research_section)
    session.flush()
    return research_section


def get_research_sections(
    session: Session,
    session_id: int,
) -> List[ResearchSection]:
    """
    Get all research sections for a session, ordered by question_id.

    Args:
        session: SQLAlchemy session (managed by caller).
        session_id: ID of the research session.

    Returns:
        List of ResearchSection objects ordered by question_id.
    """
    query = (
        select(ResearchSection)
        .where(ResearchSection.session_id == session_id)
        .order_by(ResearchSection.question_id)
    )
    result = session.execute(query).scalars().all()
    return list(result)


def update_research_section(
    session: Session,
    section_id: int,
    updates: Dict[str, Any],
) -> Optional[ResearchSection]:
    """
    Update a research section.

    Args:
        session: SQLAlchemy session (managed by caller).
        section_id: ID of the research section to update.
        updates: Dictionary of fields to update. Supported keys:
            - section_content: str
            - context_data: dict
            - matching_results: dict
            - section_metadata: dict
            - reuse_info: dict
            - quality_status: QualityStatus enum value

    Returns:
        Updated ResearchSection object or None if not found.
    """
    research_section = session.get(ResearchSection, section_id)
    if not research_section:
        return None

    allowed_fields = {
        'section_content', 'context_data', 'matching_results',
        'section_metadata', 'reuse_info', 'quality_status'
    }
    for key, value in updates.items():
        if key in allowed_fields:
            setattr(research_section, key, value)

    session.flush()
    return research_section


# --- ResearchReport CRUD ---


def create_research_report(
    session: Session,
    session_id: int,
    report_content: str,
    executive_summary: Optional[str] = None,
    quality_evaluation: Optional[Dict[str, Any]] = None,
    report_metadata: Optional[Dict[str, Any]] = None,
) -> ResearchReport:
    """
    Create a new research report for a session.

    Also updates the parent session status to 'completed' and sets completed_at.

    Args:
        session: SQLAlchemy session (managed by caller).
        session_id: ID of the parent research session.
        report_content: Full report content (required).
        executive_summary: Optional brief summary.
        quality_evaluation: Optional quality assessment data dict.
        report_metadata: Optional metadata dict.

    Returns:
        The created ResearchReport object with ID populated.
    """
    research_report = ResearchReport(
        session_id=session_id,
        report_content=report_content,
        executive_summary=executive_summary,
        quality_evaluation=quality_evaluation,
        report_metadata=report_metadata,
        version=1,
    )
    session.add(research_report)
    session.flush()

    # Extract title from report_content for easier access in lists
    import re
    title_match = re.search(r'^#\s+(.+)$', report_content, re.MULTILINE)
    report_title = title_match.group(1).strip() if title_match else "Research Report"

    # If executive_summary is not provided, try to extract a brief snippet
    if not executive_summary:
        # Remove the title if it exists at the start
        content_no_title = re.sub(r'^#\s+.+$', '', report_content, count=1, flags=re.MULTILINE).strip()
        # Take first 300 chars
        executive_summary = content_no_title[:300] + ("..." if len(content_no_title) > 300 else "")

    # Get current state_data to merge or initialize
    research_session = session.get(ResearchSession, session_id)
    current_state = research_session.state_data or {}
    
    # Update state_data with report info for the UI cards
    new_state = dict(current_state)
    new_state.update({
        'report_title': report_title,
        'executive_summary': executive_summary,
        'report_metadata': report_metadata
    })

    # Update parent session to completed
    update_research_session(
        session,
        session_id,
        {
            'status': SessionStatus.COMPLETED,
            'current_phase': ResearchPhase.COMPLETED,
            'completed_at': datetime.now(timezone.utc),
            'state_data': new_state
        }
    )

    return research_report


def get_research_report(
    session: Session,
    session_id: int,
) -> Optional[ResearchReport]:
    """
    Get the latest research report for a session (by version DESC).

    Args:
        session: SQLAlchemy session (managed by caller).
        session_id: ID of the research session.

    Returns:
        Latest ResearchReport object or None if no report exists.
    """
    query = (
        select(ResearchReport)
        .where(ResearchReport.session_id == session_id)
        .order_by(ResearchReport.version.desc())
        .limit(1)
    )
    result = session.execute(query).scalar_one_or_none()
    return result
