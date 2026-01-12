"""
Refinement Coordinator node for LangGraph workflow.

Re-plans weak sections by adjusting parameters (token budget, etc.)
and triggers re-execution of research and synthesis nodes.
"""

import logging
from typing import Dict, Any, List
from sqlalchemy.orm import Session

from ..state import ResearchState
from ...data.models.enums import ResearchPhase

logger = logging.getLogger(__name__)

# Max refinement iterations to avoid infinite loops
MAX_REFINEMENT_ITERATIONS = 2

def RefinementCoordinatorNode(state: ResearchState, session: Session) -> ResearchState:
    """
    LangGraph node to coordinate refinement of weak sections.
    
    Args:
        state: Current ResearchState.
        session: Database session.
        
    Returns:
        Updated ResearchState.
    """
    refinement_needed = state.get("refinement_needed", [])
    iteration_count = state.get("refinement_iteration_count", 0)
    
    if not refinement_needed:
        logger.info("RefinementCoordinatorNode: No refinement needed, skipping")
        new_state = state.copy()
        new_state["current_phase"] = ResearchPhase.COMPLETED.value
        return new_state
        
    # Cap refinement iterations
    if iteration_count >= MAX_REFINEMENT_ITERATIONS:
        logger.warning(f"RefinementCoordinatorNode: Max iterations ({MAX_REFINEMENT_ITERATIONS}) reached. Proceeding with current quality.")
        new_state = state.copy()
        new_state["current_phase"] = ResearchPhase.COMPLETED.value
        new_state["refinement_needed"] = []
        return new_state
        
    logger.info(f"RefinementCoordinatorNode: Coordinating refinement for {len(refinement_needed)} sections (Iteration {iteration_count + 1})")
    
    new_state = state.copy()
    research_plan = new_state.get("research_plan", {}).copy()
    sub_questions = list(research_plan.get("sub_questions", []))
    sections = new_state.get("sections", {}).copy()
    quality_metrics = new_state.get("quality_metrics", {})
    
    # Create a map for quick lookup and update
    sub_q_map = {sq["id"]: sq for sq in sub_questions}
    
    for question_id in refinement_needed:
        if question_id not in sub_q_map:
            logger.warning(f"RefinementCoordinatorNode: Question ID {question_id} not found in research plan")
            continue
            
        # Get a copy of the sub-question to modify
        sub_q = sub_q_map[question_id].copy()
        metrics = quality_metrics.get(question_id, {})
        
        # Adjust parameters based on quality metrics
        # 1. Low citation coverage: increase token budget
        if metrics.get("citation_coverage", 0) < 0.7:
            old_tokens = sub_q.get("estimated_tokens", 20000)
            sub_q["estimated_tokens"] = int(old_tokens * 1.5)
            logger.info(f"Refinement {question_id}: Increased token budget from {old_tokens} to {sub_q['estimated_tokens']}")
            
        # 2. Low source diversity: fetch additional items (simulated by hint in rationale)
        if metrics.get("source_diversity", 0) < 3:
            old_rationale = sub_q.get("rationale", "")
            if "SEEK ADDITIONAL DIVERSE SOURCES" not in old_rationale:
                sub_q["rationale"] = (old_rationale + " SEEK ADDITIONAL DIVERSE SOURCES.").strip()
                logger.info(f"Refinement {question_id}: Added diversity requirement to rationale")

        # 3. Low coherence: simplify or clarify sub-question
        if metrics.get("coherence_score") == "Low":
            old_question = sub_q.get("question", "")
            if "SIMPLIFY AND CLARIFY: " not in old_question:
                sub_q["question"] = "SIMPLIFY AND CLARIFY: " + old_question
                logger.info(f"Refinement {question_id}: Clarified question for coherence")

        # Update the sub-question in the list
        for i, sq in enumerate(sub_questions):
            if sq["id"] == question_id:
                sub_questions[i] = sub_q
                break
                
        # Clear existing section data to trigger re-execution
        if question_id in sections:
            del sections[question_id]
            logger.info(f"Refinement {question_id}: Cleared existing section content")
            
    # Update state
    research_plan["sub_questions"] = sub_questions
    new_state.update({
        "research_plan": research_plan,
        "sections": sections,
        "refinement_needed": [],
        "refinement_iteration_count": iteration_count + 1,
        "current_phase": ResearchPhase.RESEARCH.value  # Loop back to research phase
    })
    
    return new_state
