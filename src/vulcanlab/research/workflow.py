"""
LangGraph workflow for automated research orchestration.
Defines the state graph and the entry point for automated research sessions.
"""

import logging
import time
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional, Union, Callable
from functools import partial

from sqlalchemy.orm import Session
from langgraph.graph import StateGraph, END

from vulcanlab.research.state import ResearchState
from vulcanlab.research.nodes import (
    ResearchPlannerNode,
    QueryExecutorNode,
    ContextAssemblerNode,
    SynthesizerNode,
    QualityEvaluatorNode,
    RefinementCoordinatorNode,
)
from vulcanlab.data.template_loader import load_template
from vulcanlab.ai import create_langchain_chat, ModelTier
from vulcanlab.data.research_session import (
    create_research_session,
    create_research_report,
    get_research_session_by_thread_id,
    update_research_session,
)
from vulcanlab.data.models.research_session import ResearchSession
from vulcanlab.data.models.enums import SessionType, SessionStatus, ResearchPhase

logger = logging.getLogger(__name__)


class LLMClientWrapper:
    """Wrapper to provide a .generate(prompt) method for LangChain chat models."""
    
    def __init__(self, chat_model: Any):
        self.chat_model = chat_model
        
    def generate(self, prompt: str) -> str:
        """Generate response from prompt using chat model."""
        response = self.chat_model.invoke(prompt)
        content = response.content
        if isinstance(content, list):
            # Handle list content (e.g., from multimodal or part-based models)
            text_parts = []
            for part in content:
                if isinstance(part, str):
                    text_parts.append(part)
                elif isinstance(part, dict) and "text" in part:
                    text_parts.append(part["text"])
            return "".join(text_parts)
        return str(content)


def final_synthesis_node(state: ResearchState, session: Session) -> ResearchState:
    """
    LangGraph node to generate final report from all research sections.
    
    Args:
        state: Current ResearchState.
        session: Database session.
        
    Returns:
        Updated ResearchState.
    """
    collection_id = state.get("collection_id")
    thread_id = state.get("thread_id")
    
    logger.info(f"FinalSynthesisNode: STARTING for thread {thread_id}")
    
    # 1. Get all sections from state
    sections = state.get("sections")
    if not sections:
        logger.warning(f"FinalSynthesisNode: No sections found in state for final synthesis (thread {thread_id})")
        section_contents = "No research sections were generated."
    else:
        logger.info(f"FinalSynthesisNode: Found {len(sections)} sections in state")
        # Format section contents for prompt
        section_contents_list = []
        for question, data in sections.items():
            content = data.get("content", "")
            section_contents_list.append(f"## {question}\n\n{content}")
        section_contents = "\n\n".join(section_contents_list)
        
    # 2. Get research goal (collection description)
    research_goal = state.get("collection_description", "General research")
    
    # 3. Load synthesis template from database
    logger.info("FinalSynthesisNode: Loading synthesis template from database...")
    template = load_template("synthesis", fallback_builder=None)
    prompt = template.format(research_goal=research_goal, section_contents=section_contents)
    
    # 4. Get LLM client (FULL tier for synthesis with 5-minute timeout)
    logger.info("FinalSynthesisNode: Creating LLM client...")
    chat_stack = create_langchain_chat(tier=ModelTier.FULL, request_timeout=300)
    llm_client = LLMClientWrapper(chat_stack.chat)
    
    # 5. Generate report
    logger.info("FinalSynthesisNode: Generating report content...")
    report_content = llm_client.generate(prompt)
    logger.info(f"FinalSynthesisNode: Generated {len(report_content)} chars of report")
    
    # 6. Save to database
    research_session = get_research_session_by_thread_id(session, thread_id)
    if not research_session:
        logger.error(f"FinalSynthesisNode: Research session {thread_id} NOT FOUND in DB")
        raise ValueError(f"Research session with thread_id {thread_id} not found")
        
    logger.info(f"FinalSynthesisNode: Saving report to DB for session {research_session.id}")
    try:
        report = create_research_report(
            session=session,
            session_id=research_session.id,
            report_content=report_content,
        )
        # Explicitly commit here to ensure report is saved even if graph termination has issues
        session.commit()
        logger.info(f"FinalSynthesisNode: Report saved with ID {report.id} and committed")
    except Exception as e:
        logger.exception(f"FinalSynthesisNode: FATAL ERROR saving report to DB: {e}")
        session.rollback()
        raise
    
    # 7. Update state
    new_state = state.copy()
    new_state.update({
        "synthesis": report_content,
        "current_phase": ResearchPhase.COMPLETED.value
    })
    
    logger.info(f"FinalSynthesisNode: FINISHED for thread {thread_id}")
    return new_state


def should_refine(state: ResearchState) -> bool:
    """
    Conditional edge logic: should we go to refinement or finish?
    
    Args:
        state: Current ResearchState.
        
    Returns:
        True if refinement is needed and iteration limit not reached, False otherwise.
    """
    refinement_needed = state.get("refinement_needed", [])
    iteration_count = state.get("refinement_iteration_count", 0)
    
    # We use 2 as the limit, matching MAX_REFINEMENT_ITERATIONS in the coordinator node
    decision = len(refinement_needed) > 0 and iteration_count < 2
    logger.info(f"should_refine: decision={decision} (needed={len(refinement_needed)}, iterations={iteration_count})")
    return decision


def node_wrapper(state: ResearchState, node_func: Callable, session: Session) -> ResearchState:
    """
    Wraps a LangGraph node to update the research_session.current_phase in the database
    after the node executes, based on the phase stored in the state.
    """
    node_name = node_func.__name__ if hasattr(node_func, '__name__') else str(node_func)
    logger.info(f"NodeWrapper: [INVOKING] {node_name}")
    
    try:
        # Execute the node
        new_state = node_func(state, session)
        
        # Update current_phase in DB to match state
        state_phase_val = new_state.get("current_phase")
        thread_id = state.get("thread_id")
        
        if thread_id and state_phase_val:
            try:
                # Handle both Enum and string values
                if isinstance(state_phase_val, str):
                    phase_enum = ResearchPhase(state_phase_val)
                else:
                    phase_enum = state_phase_val
                    
                research_session = get_research_session_by_thread_id(session, thread_id)
                if research_session:
                    # Update phase if it has changed
                    if research_session.current_phase != phase_enum:
                        update_research_session(session, research_session.id, {"current_phase": phase_enum})
                        logger.info(f"NodeWrapper: Updated DB phase for {thread_id} to {phase_enum}")
                    
                    # ALWAYS commit after a node finishes to ensure all flushes (plan, sections, etc.)
                    # are persisted to the database.
                    session.commit()
            except Exception as db_err:
                logger.warning(f"NodeWrapper: Failed to update session phase in DB for {node_name}: {db_err}")
                
        logger.info(f"NodeWrapper: [SUCCESS] {node_name} finished. Next phase in state: {state_phase_val}")
        return new_state
    except Exception as e:
        logger.exception(f"NodeWrapper: [FATAL ERROR] in {node_name}: {e}")
        raise


def create_research_graph(session: Session) -> StateGraph:
    """
    Creates the LangGraph StateGraph for automated research.
    
    Args:
        session: Database session to be used by nodes.
        
    Returns:
        Configured StateGraph.
    """
    # Initialize graph with state schema
    workflow = StateGraph(ResearchState)
    
    # Use partials instead of closures to see if it helps LangGraph's node tracking
    # and use the actual node names as keys
    workflow.add_node("planner", partial(node_wrapper, node_func=ResearchPlannerNode, session=session))
    workflow.add_node("executor", partial(node_wrapper, node_func=QueryExecutorNode, session=session))
    workflow.add_node("assembler", partial(node_wrapper, node_func=ContextAssemblerNode, session=session))
    workflow.add_node("synthesizer", partial(node_wrapper, node_func=SynthesizerNode, session=session))
    workflow.add_node("evaluator", partial(node_wrapper, node_func=QualityEvaluatorNode, session=session))
    workflow.add_node("refiner", partial(node_wrapper, node_func=RefinementCoordinatorNode, session=session))
    workflow.add_node("final_synthesis", partial(node_wrapper, node_func=final_synthesis_node, session=session))
    
    # Set entry point
    workflow.set_entry_point("planner")
    
    # Add fixed edges
    workflow.add_edge("planner", "executor")
    workflow.add_edge("executor", "assembler")
    workflow.add_edge("assembler", "synthesizer")
    workflow.add_edge("synthesizer", "evaluator")
    
    # Add conditional edge from evaluator
    workflow.add_conditional_edges(
        "evaluator",
        should_refine,
        {
            True: "refiner",
            False: "final_synthesis"
        }
    )
    
    # Add loop edge from refiner back to executor
    workflow.add_edge("refiner", "executor")
    
    # Set finish point
    workflow.add_edge("final_synthesis", END)
    
    return workflow


def start_automated_research(collection_id: int, session: Session, session_id: Optional[int] = None):
    """
    Orchestrates the start of an automated research session.
    
    Args:
        collection_id: ID of the collection to research.
        session: Database session.
        session_id: Optional ID of an existing research session.
        
    Returns:
        tuple: (session_id, thread_id)
    """
    # 1. Determine or generate thread_id
    if session_id:
        research_session = session.get(ResearchSession, session_id)
        if not research_session:
            raise ValueError(f"Research session {session_id} not found")
        thread_id = research_session.thread_id
    else:
        timestamp = int(time.time())
        thread_id = f"auto_{collection_id}_{timestamp}"
        
        # 2. Create research session in database
        research_session = create_research_session(
            session=session,
            collection_id=collection_id,
            session_type=SessionType.AUTOMATED,
            thread_id=thread_id
        )
        session.commit()
    
    # 3. Initialize ResearchState
    initial_state: ResearchState = {
        "collection_id": collection_id,
        "collection_description": "",
        "item_notes": [],
        "research_plan": {},
        "current_phase": ResearchPhase.PLANNING.value,
        "sections": {},
        "context_per_question": {},
        "reused_sections": {},
        "available_results": [],
        "synthesis": "",
        "quality_metrics": {},
        "refinement_needed": [],
        "refinement_iteration_count": 0,
        "thread_id": thread_id
    }
    
    try:
        # 4. Compile graph WITHOUT checkpointer
        # Note: The custom PostgresSaver checkpointer has a bug that causes the graph
        # to terminate prematurely during refinement loops. Until we migrate to the
        # official langgraph-checkpoint-postgres package, we run without checkpointing.
        # This means we cannot resume mid-graph, but the research will complete properly.
        graph_builder = create_research_graph(session)
        compiled_graph = graph_builder.compile()

        # 5. Invoke graph
        # Increase recursion_limit to 1000 to handle many refinement loops
        config = {
            "configurable": {"thread_id": thread_id},
            "recursion_limit": 1000
        }

        logger.info(f"Starting research session {thread_id} (recursion_limit={config['recursion_limit']})")
        final_state = compiled_graph.invoke(initial_state, config=config)
            
        logger.info(f"Graph invocation finished for thread {thread_id}. Final state phase: {final_state.get('current_phase') if final_state else 'None'}")
            
        # 7. Final check: ensure session status and phase are updated correctly
        research_session = get_research_session_by_thread_id(session, thread_id)
        if research_session and research_session.status != SessionStatus.COMPLETED:
            # Check the phase from the session
            if research_session.current_phase == ResearchPhase.COMPLETED:
                logger.info(f"Marking session {thread_id} as completed (phase was already completed)")
                update_research_session(
                    session, 
                    research_session.id, 
                    {
                        "status": SessionStatus.COMPLETED,
                        "completed_at": datetime.now(timezone.utc)
                    }
                )
                session.commit()
            else:
                # This is a strange state: graph finished but phase is not completed
                logger.warning(f"Graph finished for {thread_id} but phase is {research_session.current_phase}. Check logs for failures.")
        
        return research_session.id, thread_id
        
    except Exception as e:
        logger.exception(f"Error in automated research for collection {collection_id} (thread {thread_id}): {e}")
        
        # 8. Update session status to failed
        # Use a fresh query to avoid session issues
        try:
            research_session = get_research_session_by_thread_id(session, thread_id)
            if research_session:
                update_research_session(
                    session,
                    research_session.id,
                    {
                        "status": SessionStatus.FAILED,
                    }
                )
                session.commit()
        except Exception as update_err:
            logger.error(f"Failed to update session status to FAILED: {update_err}")
            
        raise
