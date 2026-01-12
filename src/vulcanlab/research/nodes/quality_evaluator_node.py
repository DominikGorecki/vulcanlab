"""
Quality Evaluator node for LangGraph workflow.

Evaluates research sections for citation coverage, coherence, and completeness.
Flags sections needing refinement based on quality thresholds.
"""

import logging
from typing import Dict, Any, List
from sqlalchemy.orm import Session

from ..state import ResearchState
from ..synthesizer import evaluate_quality, check_citation_coverage
from ...data.models.enums import ResearchPhase

logger = logging.getLogger(__name__)

# Quality thresholds from spec
CITATION_COVERAGE_THRESHOLD = 0.7
SOURCE_DIVERSITY_THRESHOLD = 3
COHERENCE_SCORE_LOW = "Low"

def QualityEvaluatorNode(state: ResearchState, session: Session) -> ResearchState:
    """
    LangGraph node to evaluate research section quality.
    
    Args:
        state: Current ResearchState.
        session: Database session.
        
    Returns:
        Updated ResearchState.
    """
    logger.info("QualityEvaluatorNode: Starting quality evaluation")
    
    sections = state.get("sections", {})
    if not sections:
        logger.warning("QualityEvaluatorNode: No sections found to evaluate")
        new_state = state.copy()
        new_state["current_phase"] = ResearchPhase.SYNTHESIS.value
        new_state["refinement_needed"] = []
        return new_state
        
    quality_metrics = {}
    refinement_needed = []
    
    for question_id, section_data in sections.items():
        content = section_data.get("content", "")
        sources = section_data.get("sources", [])
        metadata = section_data.get("metadata", {})
        
        # 1. Evaluate quality metrics
        quality = evaluate_quality(content, sources, metadata)
        
        # 2. Check for broken citations
        broken_citations = check_citation_coverage(content, sources)
        quality["broken_citations"] = len(broken_citations)
        
        # 3. Store quality metrics
        quality_metrics[question_id] = quality
        
        # 4. Determine if refinement is needed
        needs_refinement = False
        
        # Use .get() with defaults to avoid KeyErrors
        if quality.get("citation_coverage", 0) < CITATION_COVERAGE_THRESHOLD:
            logger.info(f"Refinement needed for {question_id}: low citation coverage ({quality.get('citation_coverage')})")
            needs_refinement = True
        elif quality.get("source_diversity", 0) < SOURCE_DIVERSITY_THRESHOLD:
            logger.info(f"Refinement needed for {question_id}: low source diversity ({quality.get('source_diversity')})")
            needs_refinement = True
        elif quality.get("coherence_score") == COHERENCE_SCORE_LOW:
            logger.info(f"Refinement needed for {question_id}: low coherence score")
            needs_refinement = True
        elif len(broken_citations) > 0:
            logger.info(f"Refinement needed for {question_id}: {len(broken_citations)} broken citations found")
            needs_refinement = True
            
        if needs_refinement:
            refinement_needed.append(question_id)
            
    # Update and return state
    new_state = state.copy()
    new_state.update({
        "quality_metrics": quality_metrics,
        "refinement_needed": refinement_needed,
        "current_phase": ResearchPhase.REFINEMENT.value if refinement_needed else ResearchPhase.COMPLETED.value
    })
    
    logger.info(f"QualityEvaluatorNode: Evaluation complete. {len(refinement_needed)} sections need refinement. Phase set to {new_state['current_phase']}")
    
    return new_state
