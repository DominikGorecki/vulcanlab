"""
Query Executor node for LangGraph workflow.

Loops through sub-questions in the research plan, identifies matching existing results,
and decides on a reuse strategy (exact reuse, partial reuse, ensemble, or new generation).
"""

import logging
from typing import Any, Dict, List

from sqlalchemy.orm import Session

from ..result_matcher import match_results_for_question, recommend_reuse_strategy
from ..state import ResearchState
from ...data.models.result import Result
from ...data.research_session import update_research_session, get_research_session_by_thread_id
from ...data.models.enums import ResearchPhase

logger = logging.getLogger(__name__)


def QueryExecutorNode(state: ResearchState, session: Session) -> ResearchState:
    """
    LangGraph node to identify existing results for sub-questions and decide reuse strategy.
    
    Args:
        state: Current ResearchState.
        session: Database session.
        
    Returns:
        Updated ResearchState.
    """
    collection_id = state.get("collection_id")
    thread_id = state.get("thread_id")
    research_plan = state.get("research_plan", {})
    sub_questions = research_plan.get("sub_questions", [])
    
    if not collection_id:
        raise ValueError("collection_id missing from state")
    if not thread_id:
        raise ValueError("thread_id missing from state")
    
    logger.info(f"QueryExecutorNode: Processing {len(sub_questions)} sub-questions for collection {collection_id}")
    
    reused_sections = state.get("reused_sections", {})
    context_per_question = state.get("context_per_question", {})
    
    for subq in sub_questions:
        # ... (rest of the loop same)
        question_id = subq.get("id")
        question_text = subq.get("question")
        relevant_item_ids = subq.get("relevant_items", [])
        
        if not question_id or not question_text:
            continue
            
        logger.info(f"QueryExecutorNode: Matching results for {question_id}: '{question_text}'")
        
        # 1. Match existing results for this question
        matches = match_results_for_question(question_text, collection_id, session)
        
        if matches:
            # 2. Recommend reuse strategy
            strategy = recommend_reuse_strategy(matches)
            
            # 3. Store matching info
            # Note: For ensemble, we might have multiple results. 
            # The schema suggests single source_result_id, but we'll use the best one
            # and potentially store more in context_per_question.
            best_match = matches[0]
            reused_sections[question_id] = {
                "source_result_id": best_match["result_id"],
                "reuse_type": strategy,
                "similarity": best_match["similarity"],
                "quality_score": best_match["quality_score"]
            }
            
            # 4. Fetch content if reuse is high-confidence
            if strategy in ("exact_reuse", "ensemble"):
                results_to_fetch = []
                if strategy == "exact_reuse":
                    results_to_fetch = [best_match["result_id"]]
                else:  # ensemble: take top matches (e.g., up to 3)
                    results_to_fetch = [m["result_id"] for m in matches[:3]]
                
                contents = []
                for res_id in results_to_fetch:
                    result = session.get(Result, res_id)
                    if result:
                        contents.append({
                            "result_id": res_id,
                            "content": result.response_text,
                            "type": "research_result"
                        })
                context_per_question[question_id] = contents
            else:
                # partial_reuse or new_generation (if matches were low quality)
                # Prepare for context assembly (store relevant_item_ids)
                # The next node (ContextAssembly) will use this.
                context_per_question[question_id] = [
                    {"item_id": item_id, "type": "unprocessed"} 
                    for item_id in relevant_item_ids
                ]
        else:
            # No matches found
            logger.info(f"QueryExecutorNode: No matches for {question_id}, preparing for new generation")
            context_per_question[question_id] = [
                {"item_id": item_id, "type": "unprocessed"} 
                for item_id in relevant_item_ids
            ]
            
    # 5. Update research session in database
    research_session = get_research_session_by_thread_id(session, thread_id)
    if research_session:
        update_research_session(
            session,
            research_session.id,
            {
                "current_phase": ResearchPhase.CONTEXT_ASSEMBLY,
            }
        )

    # 6. Update and return state
    new_state = state.copy()
    new_state.update({
        "reused_sections": reused_sections,
        "context_per_question": context_per_question,
        "current_phase": ResearchPhase.CONTEXT_ASSEMBLY.value,
    })
    
    return new_state
