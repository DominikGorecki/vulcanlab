"""
Summarization Orchestrator for coordinating the full work summarization workflow.
"""

import enum
import logging
import time
from dataclasses import dataclass, asdict, field
from typing import List, Optional, Dict, Any
from sqlalchemy.orm import Session
from sqlalchemy import select, delete, func

from vulcanlab.data.models.summary_node import SummaryNode
from vulcanlab.data.models.work_summary import WorkSummary
from vulcanlab.data.models.sanitized_markdown import SanitizedMarkdown
from vulcanlab.summarize.node_selector import select_nodes_for_summarization, SelectedNode
from vulcanlab.summarize.evidence import build_evidence_packet
from vulcanlab.summarize.llm_summarize import summarize_node, SummaryResponse
from vulcanlab.summarize.nlp_utils import segment_sentences_with_lines
from vulcanlab.summarize.exceptions import SummarizationError, InsufficientEvidenceError

logger = logging.getLogger(__name__)

class SummarizationStatus(str, enum.Enum):
    PENDING = 'pending'
    IN_PROGRESS = 'in_progress'
    COMPLETED = 'completed'
    FAILED = 'failed'

@dataclass
class SummarizationProgress:
    work_id: int
    status: SummarizationStatus
    total_nodes: int
    completed_nodes: int
    current_node: Optional[str] = None
    error: Optional[str] = None
    total_input_tokens: int = 0
    total_output_tokens: int = 0
    failed_nodes: List[Dict[str, Any]] = field(default_factory=list)

# In-memory progress tracking for now (as per T08 notes)
_progress_cache: Dict[int, SummarizationProgress] = {}

def get_summarization_status(work_id: int, session: Session) -> Optional[SummarizationProgress]:
    """
    Returns the summarization progress for a work.
    If not in cache, checks the database for existing summary nodes.
    """
    if work_id in _progress_cache:
        return _progress_cache[work_id]
        
    # Check database for existing summary nodes
    count_stmt = select(func.count(SummaryNode.id)).where(SummaryNode.work_id == work_id)
    count = session.execute(count_stmt).scalar() or 0
    
    if count > 0:
        # If nodes exist, we assume it's completed or in a resume-able state.
        # Without a dedicated progress table, we can't know 'total_nodes' 
        # without running the node selector again.
        # For simplicity, we'll return a basic completed status if nodes exist.
        return SummarizationProgress(
            work_id=work_id,
            status=SummarizationStatus.COMPLETED,
            total_nodes=count,
            completed_nodes=count
        )
        
    return None

def delete_existing_summaries(work_id: int, session: Session) -> None:
    """
    Deletes all summary nodes and work summaries for a given work.
    Used for re-summarization.
    """
    session.execute(delete(SummaryNode).where(SummaryNode.work_id == work_id))
    session.execute(delete(WorkSummary).where(WorkSummary.work_id == work_id))
    session.commit()
    
    if work_id in _progress_cache:
        del _progress_cache[work_id]

def load_full_content(work_id: int, session: Session) -> str:
    """
    Loads the full sanitized markdown content for a work.
    """
    stmt = select(SanitizedMarkdown).where(SanitizedMarkdown.work_id == work_id)
    result = session.execute(stmt)
    sanitized = result.scalar_one_or_none()
    return sanitized.content if sanitized else ""

def create_summary_node(
    work_id: int,
    selected_node: SelectedNode,
    summary_response: SummaryResponse,
    session: Session
) -> SummaryNode:
    """
    Maps a SummaryResponse to a SummaryNode database model and saves it.
    """
    # Convert list of dataclasses to list of dicts for JSONB
    node = SummaryNode(
        chunk_id=selected_node.chunk_id,
        work_id=work_id,
        gist=summary_response.gist,
        key_points=[asdict(kp) for kp in summary_response.key_points],
        definitions=[asdict(d) for d in summary_response.definitions],
        key_terms=[asdict(kt) for kt in summary_response.key_terms],
        examples=[asdict(ex) for ex in summary_response.examples],
        start_line=selected_node.start_line,
        end_line=selected_node.end_line,
        salience_score=selected_node.salience_score
    )
    session.add(node)
    session.commit()
    return node

def process_single_node(
    work_id: int,
    node: SelectedNode,
    full_content: str,
    session: Session
) -> tuple[SummaryNode, SummaryResponse]:
    """
    Processes a single node: evidence extraction -> LLM summarization -> DB save.
    Returns (SummaryNode, SummaryResponse) to include token usage.
    """
    # 1. Build evidence packet
    sentences = segment_sentences_with_lines(node.content)
    evidence = build_evidence_packet(
        content=node.content,
        sentences_with_lines=sentences,
        heading_path=node.heading_path,
        start_line=node.start_line,
        end_line=node.end_line
    )
    
    # 2. Call LLM summarization (includes escalation logic)
    summary_response = summarize_node(
        evidence=evidence,
        session=session,
        full_content=full_content,
        chunk_id=node.chunk_id
    )
    
    # 3. Create database record
    summary_node = create_summary_node(work_id, node, summary_response, session)
    
    return summary_node, summary_response

def summarize_work(
    work_id: int, 
    session: Session, 
    force_regenerate: bool = False
) -> SummarizationProgress:
    """
    Main entry point for summarizing a work.
    """
    logger.info(f"Starting summarization for work {work_id}")
    start_time = time.time()
    
    # 1. Check existing status
    existing_status = get_summarization_status(work_id, session)
    if existing_status and not force_regenerate:
        logger.info(f"Summarization for work {work_id} already exists. Skipping.")
        return existing_status
        
    if force_regenerate:
        logger.info(f"Force regenerating summaries for work {work_id}.")
        delete_existing_summaries(work_id, session)

    # 2. Select nodes
    nodes = select_nodes_for_summarization(work_id, session)
    if not nodes:
        logger.warning(f"No nodes selected for summarization in work {work_id}.")
        progress = SummarizationProgress(
            work_id=work_id,
            status=SummarizationStatus.COMPLETED,
            total_nodes=0,
            completed_nodes=0
        )
        _progress_cache[work_id] = progress
        return progress

    logger.info(f"Selected {len(nodes)} nodes for summarization")

    # 3. Initialize progress
    progress = SummarizationProgress(
        work_id=work_id,
        status=SummarizationStatus.IN_PROGRESS,
        total_nodes=len(nodes),
        completed_nodes=0
    )
    _progress_cache[work_id] = progress
    
    # 4. Load full content for escalation
    full_content = load_full_content(work_id, session)
    
    # 5. Process nodes
    try:
        for i, node in enumerate(nodes):
            progress.current_node = f"{node.level}: {node.heading_path}"
            
            try:
                # Process single node with its own commit
                _, summary_resp = process_single_node(work_id, node, full_content, session)
                
                # Aggregate token usage
                if summary_resp.token_usage:
                    progress.total_input_tokens += summary_resp.token_usage.input_tokens
                    progress.total_output_tokens += summary_resp.token_usage.output_tokens
                
                progress.completed_nodes += 1
                logger.info(f"Completed node {i+1}/{progress.total_nodes}: {node.chunk_id}")
            except (SummarizationError, InsufficientEvidenceError) as e:
                logger.error(f"Node failure for {node.chunk_id}: {e}")
                progress.failed_nodes.append({
                    "chunk_id": node.chunk_id,
                    "heading_path": node.heading_path,
                    "error": str(e),
                    "type": type(e).__name__
                })
                # We continue to the next node on summarization-specific errors
                continue
            except Exception as e:
                # For unexpected errors (DB, etc.), we fail the whole process
                logger.error(f"Unexpected error processing node {node.chunk_id}: {e}")
                progress.status = SummarizationStatus.FAILED
                progress.error = str(e)
                raise

        duration = time.time() - start_time
        
        # Mark as completed even if some nodes failed, as long as we finished the loop
        # We can distinguish partial completion by looking at failed_nodes
        progress.status = SummarizationStatus.COMPLETED
        progress.current_node = None
        
        if progress.failed_nodes:
            logger.warning(f"Summarization completed with {len(progress.failed_nodes)} failed nodes.")
        
        logger.info(f"Summarization completed for work {work_id} in {duration:.2f}s")
        logger.info(f"Total token usage for work {work_id}: input={progress.total_input_tokens}, output={progress.total_output_tokens}")
        
    except Exception as e:
        if progress.status != SummarizationStatus.FAILED:
            logger.error(f"Summarization failed for node {progress.current_node or 'unknown'}: {e}")
            progress.status = SummarizationStatus.FAILED
            progress.error = str(e)
        raise

    return progress

def resume_summarization(work_id: int, session: Session) -> SummarizationProgress:
    """
    Resumes summarization from the last successful node.
    """
    logger.info(f"Resuming summarization for work {work_id}")
    start_time = time.time()

    # 1. Get all nodes that should be summarized
    all_nodes = select_nodes_for_summarization(work_id, session)
    if not all_nodes:
        return summarize_work(work_id, session)
        
    # 2. Find which nodes are already summarized
    stmt = select(SummaryNode.chunk_id).where(SummaryNode.work_id == work_id)
    completed_chunk_ids = set(session.execute(stmt).scalars().all())
    
    remaining_nodes = [n for n in all_nodes if n.chunk_id not in completed_chunk_ids]
    
    if not remaining_nodes:
        logger.info(f"No remaining nodes to summarize for work {work_id}.")
        return get_summarization_status(work_id, session)
        
    # 3. Initialize progress
    progress = SummarizationProgress(
        work_id=work_id,
        status=SummarizationStatus.IN_PROGRESS,
        total_nodes=len(all_nodes),
        completed_nodes=len(all_nodes) - len(remaining_nodes)
    )
    _progress_cache[work_id] = progress
    
    # 4. Process remaining
    full_content = load_full_content(work_id, session)
    
    try:
        for i, node in enumerate(remaining_nodes):
            progress.current_node = f"{node.level}: {node.heading_path}"
            try:
                _, summary_resp = process_single_node(work_id, node, full_content, session)
                
                # Aggregate token usage for the resumed part
                if summary_resp.token_usage:
                    progress.total_input_tokens += summary_resp.token_usage.input_tokens
                    progress.total_output_tokens += summary_resp.token_usage.output_tokens
                
                progress.completed_nodes += 1
                logger.info(f"Completed node {progress.completed_nodes}/{progress.total_nodes}: {node.chunk_id} (Resume)")
            except (SummarizationError, InsufficientEvidenceError) as e:
                logger.error(f"Node failure for {node.chunk_id} (Resume): {e}")
                progress.failed_nodes.append({
                    "chunk_id": node.chunk_id,
                    "heading_path": node.heading_path,
                    "error": str(e),
                    "type": type(e).__name__
                })
                continue
            except Exception as e:
                logger.error(f"Unexpected error processing node {node.chunk_id} (Resume): {e}")
                progress.status = SummarizationStatus.FAILED
                progress.error = str(e)
                raise
            
        duration = time.time() - start_time
        progress.status = SummarizationStatus.COMPLETED
        progress.current_node = None
        
        if progress.failed_nodes:
            logger.warning(f"Resume completed with {len(progress.failed_nodes)} failed nodes.")
            
        logger.info(f"Resume completed for work {work_id} in {duration:.2f}s")
        logger.info(f"Token usage for this resume session: input={progress.total_input_tokens}, output={progress.total_output_tokens}")
        
    except Exception as e:
        if progress.status != SummarizationStatus.FAILED:
            logger.error(f"Resume failed for node {progress.current_node or 'unknown'}: {e}")
            progress.status = SummarizationStatus.FAILED
            progress.error = str(e)
        raise
        
    return progress
