"""
Context Assembler node for LangGraph workflow.

Consolidates context for each sub-question, applies token limits, 
and deduplicates using the context_assembler module.
"""

import logging
from typing import Any, Dict

from sqlalchemy.orm import Session

from ..context_assembler import assemble_context_for_question
from ..state import ResearchState
from ...data.models.enums import ResearchPhase

logger = logging.getLogger(__name__)


def ContextAssemblerNode(state: ResearchState, session: Session) -> ResearchState:
    """
    LangGraph node to assemble context for all sub-questions.
    
    Args:
        state: Current ResearchState.
        session: Database session.
        
    Returns:
        Updated ResearchState.
    """
    logger.info("ContextAssemblerNode: Assembling context for sub-questions")
    
    research_plan = state.get("research_plan", {})
    sub_questions = research_plan.get("sub_questions", [])
    
    if not sub_questions:
        logger.warning("No sub-questions found in research plan")
        new_state = state.copy()
        new_state["context_per_question"] = {}
        new_state["current_phase"] = ResearchPhase.SYNTHESIS.value
        return new_state

    # Use a copy to avoid in-place modification of state
    context_per_question = state.get("context_per_question", {}).copy()
    reused_sections = state.get("reused_sections", {})
    sections = state.get("sections", {})
    
    for sub_q in sub_questions:
        question_id = sub_q.get("question_id") or sub_q.get("id")
        if not question_id:
            logger.warning(f"Sub-question missing identifier: {sub_q}")
            continue
            
        # Optimization: if we already have a section for this question, we might skip assembly
        # BUT only if refinement hasn't cleared it.
        if question_id in sections and sections[question_id].get("content"):
            logger.info(f"ContextAssemblerNode: Question {question_id} already has content, skipping assembly")
            continue

        relevant_item_ids = sub_q.get("relevant_items") or sub_q.get("relevant_item_ids") or []
        reuse_info = reused_sections.get(question_id)
        
        try:
            context_result = assemble_context_for_question(
                question_id=int(question_id) if isinstance(question_id, str) and question_id.isdigit() else question_id,
                relevant_item_ids=relevant_item_ids,
                reuse_info=reuse_info,
                session=session
            )
            context_per_question[question_id] = context_result
            logger.info(f"ContextAssemblerNode: Assembled {context_result.get('token_count', 0)} tokens for {question_id}")
        except Exception as e:
            logger.error(f"Error assembling context for question {question_id}: {e}")
            # Initialize with empty data to avoid key errors in subsequent nodes
            context_per_question[question_id] = {
                "context": "",
                "token_count": 0,
                "sources": []
            }

    # Update and return state
    new_state = state.copy()
    new_state.update({
        "context_per_question": context_per_question,
        "current_phase": ResearchPhase.SYNTHESIS.value,
    })
    
    logger.info(f"ContextAssemblerNode: Finished. Phase set to {new_state['current_phase']}")
    
    return new_state
