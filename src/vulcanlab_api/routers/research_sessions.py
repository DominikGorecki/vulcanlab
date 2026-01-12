"""
Research Sessions Router - Core CRUD endpoints for research workflows.
"""

from typing import List, Optional

from fastapi import APIRouter, Depends, HTTPException, status, BackgroundTasks, Query
from sqlalchemy.orm import Session

from vulcanlab.data.database import get_db_session, get_session
from vulcanlab.data.models.enums import SessionType, SessionStatus, ResearchPhase
from vulcanlab.data.research_session import (
    create_research_session as core_create_research_session,
    get_research_session as core_get_research_session,
    update_research_session as core_update_research_session,
    list_research_sessions_for_collection as core_list_research_sessions,
    create_research_section as core_create_research_section,
    get_research_sections as core_get_research_sections,
    create_research_report as core_create_research_report,
    get_research_report as core_get_research_report,
    generate_thread_id,
)
from vulcanlab.collections import get_collection as core_get_collection
from vulcanlab.data.template_loader import load_template
from vulcanlab.research.research_planner import (
    analyze_collection as core_analyze_collection,
    prepare_template_variables,
)
from vulcanlab.research.synthesizer import format_sources_list
from vulcanlab.research.context_assembler import assemble_context_for_question
from vulcanlab.research.result_matcher import (
    match_results_for_question,
    recommend_reuse_strategy,
)
from vulcanlab.research.workflow import start_automated_research
from vulcanlab_api.schemas.research_sessions import (
    CreateResearchSessionRequest,
    ResearchSessionResponse,
    UpdateResearchSessionRequest,
    ResearchSessionListResponse,
    CreateResearchSectionRequest,
    ResearchSectionResponse,
    ResearchSectionListResponse,
    CreateResearchReportRequest,
    ResearchReportResponse,
    AssembleContextRequest,
    AssembleContextResponse,
    MatchResultsRequest,
    MatchResultsResponse,
    ResumeSessionRequest,
    ResumeSessionResponse,
    StartAutomatedResearchRequest,
    StartAutomatedResearchResponse,
    FormattedPromptResponse,
)

import logging
logger = logging.getLogger(__name__)

router = APIRouter()


# --- Helper for Authorization ---
def verify_collection_access(collection_id: int, db: Session):
    """
    Verify that the collection exists and the user has access to it.
    
    NOTE: Currently a placeholder as there is no user system.
    In the future, this would check if collection.owner_id == current_user_id.
    """
    collection = core_get_collection(db, collection_id)
    if not collection:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Collection {collection_id} not found"
        )
    return collection


# --- Background Tasks ---

def run_automated_research_task(collection_id: int, session_id: int):
    """Background task to run the automated research workflow."""
    with get_session() as db:
        try:
            logger.info(f"Starting automated research background task for session {session_id}")
            # The workflow module handles the graph execution and state updates
            start_automated_research(collection_id=collection_id, session=db, session_id=session_id)
            
            # Explicitly commit the final state (status=COMPLETED, etc.) set by the workflow
            db.commit()
            
            logger.info(f"Automated research background task for session {session_id} completed successfully")
        except Exception as e:
            logger.error(f"Error in automated research background task for session {session_id}: {e}")
            # Ensure status is updated to FAILED if not already handled
            try:
                core_update_research_session(db, session_id, {
                    "status": SessionStatus.FAILED,
                    "state_data": {"error": str(e)}
                })
                db.commit()
            except Exception as commit_err:
                logger.error(f"Failed to update session status after background error: {commit_err}")


# --- Research Session Endpoints ---

@router.post(
    "/research-sessions/start-automated",
    response_model=StartAutomatedResearchResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Start automated research",
    tags=["Research Sessions"]
)
async def start_automated_session(
    request: StartAutomatedResearchRequest,
    background_tasks: BackgroundTasks,
    db: Session = Depends(get_db_session)
):
    """
    Start an automated research session for a collection.
    Executes the LangGraph workflow in the background.
    """
    verify_collection_access(request.collection_id, db)
    
    # Create the session first so we can return the ID immediately
    thread_id = generate_thread_id(SessionType.AUTOMATED, request.collection_id)
    
    research_session = core_create_research_session(
        session=db,
        collection_id=request.collection_id,
        session_type=SessionType.AUTOMATED,
        thread_id=thread_id
    )
    db.commit()
    
    # Add background task
    background_tasks.add_task(
        run_automated_research_task, 
        collection_id=request.collection_id, 
        session_id=research_session.id
    )
    
    return StartAutomatedResearchResponse(
        session_id=research_session.id,
        thread_id=thread_id,
        status="in_progress",
        message="Automated research started"
    )


@router.post(
    "/research-sessions",
    response_model=ResearchSessionResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Create research session",
    tags=["Research Sessions"]
)
async def create_session(
    request: CreateResearchSessionRequest,
    db: Session = Depends(get_db_session)
):
    """Create a new research session for a collection."""
    verify_collection_access(request.collection_id, db)
    
    try:
        session_type = SessionType(request.session_type)
    except ValueError:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Invalid session_type: {request.session_type}. Must be 'manual' or 'automated'."
        )
    
    thread_id = generate_thread_id(session_type, request.collection_id)
    
    research_session = core_create_research_session(
        session=db,
        collection_id=request.collection_id,
        session_type=session_type,
        thread_id=thread_id
    )
    db.commit()
    
    return ResearchSessionResponse.model_validate(research_session)


@router.get(
    "/research-sessions/{session_id}",
    response_model=ResearchSessionResponse,
    summary="Get research session",
    tags=["Research Sessions"]
)
async def get_research_session_endpoint(
    session_id: int,
    db: Session = Depends(get_db_session)
):
    """Retrieve a specific research session by ID."""
    research_session = core_get_research_session(db, session_id)
    if not research_session:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Research session {session_id} not found"
        )
    
    # Verify access to the parent collection
    verify_collection_access(research_session.collection_id, db)
    
    return ResearchSessionResponse.model_validate(research_session)


@router.put(
    "/research-sessions/{session_id}",
    response_model=ResearchSessionResponse,
    summary="Update research session",
    tags=["Research Sessions"]
)
async def update_session(
    session_id: int,
    request: UpdateResearchSessionRequest,
    db: Session = Depends(get_db_session)
):
    """Update research session state (phase, plan, state_data, status)."""
    research_session = core_get_research_session(db, session_id)
    if not research_session:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Research session {session_id} not found"
        )
    
    verify_collection_access(research_session.collection_id, db)
    
    updates = request.model_dump(exclude_unset=True)
    updated_session = core_update_research_session(db, session_id, updates)
    db.commit()
    
    return ResearchSessionResponse.model_validate(updated_session)


@router.get(
    "/collections/{collection_id}/research-sessions",
    response_model=ResearchSessionListResponse,
    summary="List sessions for collection",
    tags=["Collections"]
)
async def list_collection_sessions(
    collection_id: int,
    db: Session = Depends(get_db_session)
):
    """List all research sessions for a specific collection."""
    verify_collection_access(collection_id, db)
    
    sessions = core_list_research_sessions(db, collection_id)
    return ResearchSessionListResponse(
        sessions=[ResearchSessionResponse.model_validate(s) for s in sessions]
    )


# --- Manual Wizard & Workflow Endpoints ---

@router.get(
    "/collections/{collection_id}/analyze",
    summary="Analyze collection for research planning",
    tags=["Collections"]
)
async def analyze_collection_for_research(
    collection_id: int,
    db: Session = Depends(get_db_session)
):
    """
    Perform a deep analysis of a collection to prepare for research planning.
    Returns metadata, item summaries, and counts.
    """
    verify_collection_access(collection_id, db)
    try:
        analysis = core_analyze_collection(collection_id, db)
        return analysis
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(e)
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Analysis failed: {str(e)}"
        )


@router.get(
    "/research-sessions/{session_id}/prompts/{function_tag}",
    response_model=FormattedPromptResponse,
    summary="Get formatted prompt for a session step",
    tags=["Research Sessions"]
)
async def get_formatted_prompt(
    session_id: int,
    function_tag: str,
    question_id: Optional[str] = Query(None),
    db: Session = Depends(get_db_session)
):
    """
    Get a formatted prompt for a specific step in the research workflow.
    Automatically fetches the active template from the DB and fills it with 
    the session's current context.
    """
    research_session = core_get_research_session(db, session_id)
    if not research_session:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Research session {session_id} not found"
        )
    
    verify_collection_access(research_session.collection_id, db)

    try:
        template = load_template(function_tag)
        
        if function_tag == "research_planning":
            analysis = core_analyze_collection(research_session.collection_id, db)
            template_vars = prepare_template_variables(analysis)
            prompt = template.format(**template_vars)
            
        elif function_tag == "section_synthesis":
            if not question_id:
                raise HTTPException(status_code=400, detail="question_id is required for section_synthesis")
            
            # Find the question in the plan
            plan = research_session.research_plan or {}
            subqs = plan.get("sub_questions", [])
            subq = next((q for q in subqs if q.get("id") == question_id), None)
            
            if not subq:
                raise HTTPException(status_code=404, detail=f"Question {question_id} not found in plan")
            
            # Get context for this question
            reuse_info = (research_session.state_data or {}).get("reuse_info", {}).get(question_id)
            context_data = assemble_context_for_question(
                question_id=0,
                relevant_item_ids=subq.get("relevant_items", []),
                reuse_info=reuse_info,
                session=db
            )
            
            prompt = template.format(
                question_text=subq.get("question", ""),
                context=context_data["context"],
                sources_list=format_sources_list(context_data["sources"])
            )
            
        elif function_tag == "synthesis":
            # Final report synthesis
            research_goal = (research_session.research_plan or {}).get("research_goal", "General research")
            
            # Get all sections
            sections = core_get_research_sections(db, session_id)
            section_contents_list = []
            for s in sections:
                section_contents_list.append(f"## {s.question_text}\n\n{s.section_content}")
            
            section_contents = "\n\n".join(section_contents_list) if section_contents_list else "No sections generated."
            
            prompt = template.format(
                research_goal=research_goal,
                section_contents=section_contents
            )
        elif function_tag == "quality_evaluation":
            # Quality evaluation of the final report
            report = core_get_research_report(db, session_id)
            if not report:
                # Fallback to current sections if report not saved yet
                sections = core_get_research_sections(db, session_id)
                report_content = "\n\n".join([f"## {s.question_text}\n\n{s.section_content}" for s in sections])
            else:
                report_content = report.report_content

            # For quality evaluation, we want to show what sources were used
            # We'll gather unique sources from all sections
            sections = core_get_research_sections(db, session_id)
            all_sources = {}
            for s in sections:
                if s.context_data and "sources" in s.context_data:
                    # context_data["sources"] is a list of dicts
                    for source in s.context_data["sources"]:
                        # Use item_id or work_id for deduplication
                        src_id = source.get("item_id") or source.get("work_id") or str(source)
                        all_sources[src_id] = source
            
            # Match variable names used in validate_research_templates.py and standard seeding
            # format_sources_list expects a list, so convert dict values
            prompt = template.format(
                content=report_content,
                sources_list=format_sources_list(list(all_sources.values()))
            )
            logger.info(f"Generated quality_evaluation prompt (first 100 chars): {prompt[:100]}...")
        else:
            raise HTTPException(status_code=400, detail=f"Unsupported function_tag for prompt preview: {function_tag}")

        return FormattedPromptResponse(prompt=prompt, function_tag=function_tag)

    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        logger.error(f"Error formatting prompt: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to format prompt: {str(e)}")


@router.post(
    "/research-sessions/{session_id}/context",
    response_model=AssembleContextResponse,
    summary="Assemble context for a question",
    tags=["Research Sessions"]
)
async def assemble_context(
    session_id: int,
    request: AssembleContextRequest,
    db: Session = Depends(get_db_session)
):
    """
    Assemble and truncate context for a specific question in a session.
    Used by manual wizard Step 3.
    """
    research_session = core_get_research_session(db, session_id)
    if not research_session:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Research session {session_id} not found"
        )
    
    verify_collection_access(research_session.collection_id, db)
    
    # Check for reuse_info in session state
    reuse_info = None
    if research_session.state_data:
        reuse_info = research_session.state_data.get("reuse_info", {}).get(request.question_id)
    
    # Call core module
    result = assemble_context_for_question(
        question_id=0,  # Placeholder, not currently used by core module
        relevant_item_ids=request.relevant_item_ids,
        reuse_info=reuse_info,
        session=db
    )
    
    return AssembleContextResponse(**result)


@router.post(
    "/research-sessions/{session_id}/match-results",
    response_model=MatchResultsResponse,
    summary="Match existing results for a question",
    tags=["Research Sessions"]
)
async def match_results(
    session_id: int,
    request: MatchResultsRequest,
    db: Session = Depends(get_db_session)
):
    """
    Identify existing research results that match a sub-question.
    Used by manual wizard Step 2.
    """
    research_session = core_get_research_session(db, session_id)
    if not research_session:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Research session {session_id} not found"
        )
    
    verify_collection_access(research_session.collection_id, db)
    
    # Call core module
    matched_results = match_results_for_question(
        question_text=request.question_text,
        collection_id=research_session.collection_id,
        session=db
    )
    
    recommended_strategy = recommend_reuse_strategy(matched_results)
    
    return MatchResultsResponse(
        matched_results=matched_results,
        recommended_strategy=recommended_strategy
    )


@router.post(
    "/research-sessions/{session_id}/resume",
    response_model=ResumeSessionResponse,
    summary="Resume research session",
    tags=["Research Sessions"]
)
async def resume_session(
    session_id: int,
    request: ResumeSessionRequest,
    db: Session = Depends(get_db_session)
):
    """
    Resume a research session and determine the next step.
    Supports switching between manual and automated modes.
    """
    research_session = core_get_research_session(db, session_id)
    if not research_session:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Research session {session_id} not found"
        )
    
    verify_collection_access(research_session.collection_id, db)
    
    # Handle mode switch if requested
    if request.mode:
        try:
            new_mode = SessionType(request.mode)
            if new_mode != research_session.session_type:
                core_update_research_session(db, session_id, {"session_type": new_mode})
                db.commit()
                # Refresh session object
                research_session = core_get_research_session(db, session_id)
        except ValueError:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Invalid mode: {request.mode}. Must be 'manual' or 'automated'."
            )
    
    # Determine next step based on current phase
    current_phase = research_session.current_phase or ResearchPhase.PLANNING
    next_step = {"step": "unknown"}
    
    if current_phase == ResearchPhase.PLANNING:
        # Planning complete, move to result matching for first question
        first_q_id = "Q1"
        if research_session.research_plan and "sub_questions" in research_session.research_plan:
            subqs = research_session.research_plan["sub_questions"]
            if subqs:
                first_q_id = subqs[0].get("id", "Q1")
        
        next_step = {
            "step": "result_matching",
            "question_id": first_q_id
        }
    
    elif current_phase == ResearchPhase.RESEARCH:
        # Find the first question that doesn't have a section yet
        sections = core_get_research_sections(db, session_id)
        completed_q_ids = {s.question_id for s in sections}
        
        next_q_id = None
        if research_session.research_plan and "sub_questions" in research_session.research_plan:
            for subq in research_session.research_plan["sub_questions"]:
                if subq.get("id") not in completed_q_ids:
                    next_q_id = subq.get("id")
                    break
        
        if next_q_id:
            next_step = {
                "step": "section_generation",
                "question_id": next_q_id
            }
        else:
            # All questions answered, move to synthesis
            next_step = {
                "step": "synthesis_preparation"
            }
            
    elif current_phase == ResearchPhase.SYNTHESIS:
        next_step = {
            "step": "quality_evaluation"
        }
    
    return ResumeSessionResponse(
        session_id=session_id,
        current_phase=current_phase.value if hasattr(current_phase, 'value') else current_phase,
        next_step=next_step
    )


# --- Research Section Endpoints ---

@router.post(
    "/research-sessions/{session_id}/sections",
    response_model=ResearchSectionResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Save research section",
    tags=["Research Sessions"]
)
async def save_section(
    session_id: int,
    request: CreateResearchSectionRequest,
    db: Session = Depends(get_db_session)
):
    """Save a new research section for a session."""
    research_session = core_get_research_session(db, session_id)
    if not research_session:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Research session {session_id} not found"
        )
    
    verify_collection_access(research_session.collection_id, db)
    
    section = core_create_research_section(
        session=db,
        session_id=session_id,
        question_id=request.question_id,
        question_text=request.question_text,
        section_content=request.section_content,
        context_data=request.context_data,
        matching_results=request.matching_results,
        section_metadata=request.metadata,
        reuse_info=request.reuse_info
    )
    db.commit()
    
    return ResearchSectionResponse.model_validate(section)


@router.get(
    "/research-sessions/{session_id}/sections",
    response_model=ResearchSectionListResponse,
    summary="List research sections",
    tags=["Research Sessions"]
)
async def list_sections(
    session_id: int,
    db: Session = Depends(get_db_session)
):
    """Get all research sections for a session."""
    research_session = core_get_research_session(db, session_id)
    if not research_session:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Research session {session_id} not found"
        )
    
    verify_collection_access(research_session.collection_id, db)
    
    sections = core_get_research_sections(db, session_id)
    return ResearchSectionListResponse(
        sections=[ResearchSectionResponse.model_validate(s) for s in sections]
    )


# --- Research Report Endpoints ---

def generate_synthesis_report_markdown(research_session, db: Session) -> str:
    """
    Generate the 'Synthesis Report' markdown which shows what goes into the synthesis prompt.
    """
    # 1. Get research goal (collection description)
    collection = core_get_collection(db, research_session.collection_id)
    research_goal = collection.description if collection and collection.description else "General research"
    
    # 2. Format section contents
    # We use research_session.sections which is a relationship
    sections = research_session.sections
    section_contents_list = []
    
    # Sort sections by question_id if possible (Q1, Q2, etc.)
    sorted_sections = sorted(sections, key=lambda s: s.question_id or "")
    
    for section in sorted_sections:
        question = section.question_text or "Unknown Question"
        content = section.section_content or "No content generated."
        section_contents_list.append(f"## {question}\n\n{content}")
        
    section_contents = "\n\n".join(section_contents_list)
    
    # 3. Assemble the markdown
    markdown = f"# Synthesis Report\n\n**Goal:** {research_goal}\n\n## Contents\n\n{section_contents}"
    return markdown


@router.post(
    "/research-sessions/{session_id}/report",
    response_model=ResearchReportResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Save research report",
    tags=["Research Sessions"]
)
async def save_report(
    session_id: int,
    request: CreateResearchReportRequest,
    db: Session = Depends(get_db_session)
):
    """Save the final research report and mark session as completed."""
    research_session = core_get_research_session(db, session_id)
    if not research_session:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Research session {session_id} not found"
        )
    
    verify_collection_access(research_session.collection_id, db)
    
    report = core_create_research_report(
        session=db,
        session_id=session_id,
        report_content=request.report_content,
        executive_summary=request.executive_summary,
        quality_evaluation=request.quality_evaluation,
        report_metadata=request.metadata
    )
    db.commit()
    
    # Generate synthesis report for response
    synthesis_report = generate_synthesis_report_markdown(research_session, db)
    
    response_data = ResearchReportResponse.model_validate(report)
    response_data.synthesis_report = synthesis_report
    response_data.collection_id = research_session.collection_id
    
    # Get collection name for response
    collection = core_get_collection(db, research_session.collection_id)
    response_data.collection = {
        "id": collection.id,
        "name": collection.name
    } if collection else None
    
    return response_data


@router.get(
    "/research-sessions/{session_id}/report",
    response_model=ResearchReportResponse,
    summary="Get research report",
    tags=["Research Sessions"]
)
async def get_report(
    session_id: int,
    db: Session = Depends(get_db_session)
):
    """Retrieve the latest research report for a session."""
    research_session = core_get_research_session(db, session_id)
    if not research_session:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Research session {session_id} not found"
        )
    
    verify_collection_access(research_session.collection_id, db)
    
    report = core_get_research_report(db, session_id)
    if not report:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"No report found for session {session_id}"
        )
    
    # Generate synthesis report for response
    synthesis_report = generate_synthesis_report_markdown(research_session, db)
    
    response_data = ResearchReportResponse.model_validate(report)
    response_data.synthesis_report = synthesis_report
    response_data.collection_id = research_session.collection_id
    
    # Get collection name for response
    collection = core_get_collection(db, research_session.collection_id)
    response_data.collection = {
        "id": collection.id,
        "name": collection.name
    } if collection else None
    
    return response_data
