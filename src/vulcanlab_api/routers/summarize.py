import logging
from typing import List
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from sqlalchemy import select, func

from vulcanlab_api.dependencies import get_db_session
from vulcanlab.data.models.work import Work
from vulcanlab.data.models.summary_node import SummaryNode
from vulcanlab.data.models.work_summary import WorkSummary
from vulcanlab.summarize import orchestrator, compile
from vulcanlab.summarize.orchestrator import SummarizationStatus
from vulcanlab.summarize.exceptions import format_summarization_error
from vulcanlab_api.schemas.summarize import (
    SummarizationTriggerResponse,
    SummarizationStatusResponse,
    SummaryNodesResponse,
    DeriveRequest,
    DeriveResponse,
    WorkSummaryResponse,
    SummarizedWorksResponse,
    SummarizedWorkResponse,
    SuccessResponse
)

router = APIRouter()
logger = logging.getLogger(__name__)

# --- Endpoints ---

@router.post("/{work_id}", response_model=SummarizationTriggerResponse, tags=["Summarize"])
async def trigger_summarization(
    work_id: int,
    force: bool = Query(False, description="Force re-summarization"),
    db: Session = Depends(get_db_session)
):
    """Trigger summarization for a work."""
    # Validate work exists
    work = db.get(Work, work_id)
    if not work:
        raise HTTPException(status_code=404, detail=f"Work {work_id} not found")

    # Check if already summarized
    status = orchestrator.get_summarization_status(work_id, db)
    if status and status.status == SummarizationStatus.COMPLETED and not force:
        return SummarizationTriggerResponse(
            status=status.status.value,
            message=f"Summarization for work {work_id} already exists."
        )

    # Call orchestrator
    # Note: orchestrator.summarize_work is currently synchronous.
    # In a real app, this should probably be backgrounded, but following T11 plan.
    try:
        progress = orchestrator.summarize_work(work_id, db, force_regenerate=force)
        
        message = "Summarization completed"
        if progress.failed_nodes:
            message = f"Summarization completed with {len(progress.failed_nodes)} partial failures."
            
        return SummarizationTriggerResponse(
            status=progress.status.value,
            message=message
        )
    except Exception as e:
        logger.error(f"Summarization error for work {work_id}: {e}")
        error_msg = format_summarization_error(e)
        raise HTTPException(status_code=500, detail=error_msg)

@router.get("/{work_id}/status", response_model=SummarizationStatusResponse, tags=["Summarize"])
async def get_status(work_id: int, db: Session = Depends(get_db_session)):
    """Get summarization status for a work."""
    status = orchestrator.get_summarization_status(work_id, db)
    if not status:
        raise HTTPException(status_code=404, detail=f"No summarization found for work {work_id}")
    
    return SummarizationStatusResponse(
        status=status.status.value,
        total_nodes=status.total_nodes,
        completed_nodes=status.completed_nodes,
        error=status.error
    )

@router.get("/{work_id}/nodes", response_model=SummaryNodesResponse, tags=["Summarize"])
async def get_nodes(work_id: int, db: Session = Depends(get_db_session)):
    """Get all summary nodes for a work."""
    nodes = compile.load_summary_nodes(work_id, db)
    return SummaryNodesResponse(nodes=nodes)

@router.post("/{work_id}/derive", response_model=DeriveResponse, tags=["Summarize"])
async def derive_output(
    work_id: int,
    request: DeriveRequest,
    db: Session = Depends(get_db_session)
):
    """Generate derived output for a work."""
    # Check if summary nodes exist
    nodes = compile.load_summary_nodes(work_id, db)
    if not nodes:
        raise HTTPException(status_code=400, detail=f"No summary nodes found for work {work_id}. Summarize the work first.")

    try:
        summary = compile.generate_derived_output(work_id, request.type, db)
        db.commit() # Ensure changes are saved
        return summary
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/{work_id}/summaries", response_model=List[WorkSummaryResponse], tags=["Summarize"])
async def get_summaries(work_id: int, db: Session = Depends(get_db_session)):
    """Get all derived summaries for a work."""
    summaries = compile.get_derived_outputs(work_id, db)
    return summaries

@router.get("/works", response_model=SummarizedWorksResponse, tags=["Summarize"])
async def list_summarized_works(db: Session = Depends(get_db_session)):
    """List works that have at least one summary node."""
    # Query works that have summary nodes
    stmt = (
        select(Work.id, Work.title, func.count(SummaryNode.id).label("node_count"))
        .join(SummaryNode, Work.id == SummaryNode.work_id)
        .group_by(Work.id, Work.title)
    )
    results = db.execute(stmt).all()
    
    works = []
    for row in results:
        # Get available summary types
        summary_stmt = select(WorkSummary.type).where(WorkSummary.work_id == row.id)
        summaries = db.execute(summary_stmt).scalars().all()
        
        works.append(SummarizedWorkResponse(
            work_id=row.id,
            title=row.title,
            node_count=row.node_count,
            summaries=[s.value if hasattr(s, 'value') else str(s) for s in summaries]
        ))
        
    return SummarizedWorksResponse(works=works)

@router.delete("/{work_id}", response_model=SuccessResponse, tags=["Summarize"])
async def delete_summaries(work_id: int, db: Session = Depends(get_db_session)):
    """Delete all summaries for a work."""
    orchestrator.delete_existing_summaries(work_id, db)
    return SuccessResponse(message=f"Summaries deleted for work {work_id}")
