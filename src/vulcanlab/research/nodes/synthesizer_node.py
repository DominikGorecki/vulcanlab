"""
Synthesizer node for LangGraph workflow.

Generates research section content via LLM, saves to research_sections, 
and extracts metadata using the synthesizer module.
"""

import logging
from typing import Any, Dict

from sqlalchemy.orm import Session

from ..synthesizer import generate_section, extract_metadata
from ..state import ResearchState
from ...ai import create_langchain_chat, ModelTier
from ...data.research_session import create_research_section, get_research_session_by_thread_id
from ...data.models.enums import ResearchPhase

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


def SynthesizerNode(state: ResearchState, session: Session) -> ResearchState:
    """
    LangGraph node to generate and save research sections.
    
    Args:
        state: Current ResearchState.
        session: Database session.
        
    Returns:
        Updated ResearchState.
    """
    thread_id = state.get("thread_id")
    if not thread_id:
        raise ValueError("thread_id missing from state")
        
    logger.info(f"SynthesizerNode: Generating sections for thread {thread_id}")
    
    # 1. Get research session from database
    research_session = get_research_session_by_thread_id(session, thread_id)
    if not research_session:
        raise ValueError(f"Research session with thread_id {thread_id} not found")
        
    research_plan = state.get("research_plan", {})
    sub_questions = research_plan.get("sub_questions", [])
    num_questions = len(sub_questions)
    
    if not sub_questions:
        logger.warning("No sub-questions found in research plan")
        new_state = state.copy()
        new_state["current_phase"] = ResearchPhase.EVALUATION.value
        return new_state

    # 2. Get LLM client (FULL tier for synthesis with 5-minute timeout)
    chat_stack = create_langchain_chat(tier=ModelTier.FULL, request_timeout=300)
    llm_client = LLMClientWrapper(chat_stack.chat)
    
    # Use a copy of sections to avoid modifying original state object in place
    sections = state.get("sections")
    if sections is None:
        sections = {}
    else:
        sections = sections.copy()
        
    context_per_question = state.get("context_per_question", {})
    if context_per_question is None:
        context_per_question = {}
        
    reused_sections = state.get("reused_sections", {})
    if reused_sections is None:
        reused_sections = {}
    
    logger.info(f"SynthesizerNode: Context keys available: {list(context_per_question.keys())}")
    
    for i, sub_q in enumerate(sub_questions):
        question_id = sub_q.get("question_id") or sub_q.get("id")
        question_text = sub_q.get("question", "")
        
        if not question_id:
            continue
            
        # IMPORTANT: Skip if already successfully synthesized in a previous iteration
        # and NOT cleared by RefinementCoordinator.
        if question_id in sections and sections[question_id].get("content"):
            logger.info(f"SynthesizerNode: Skipping {question_id}, already has content")
            continue

        logger.info(f"SynthesizerNode: Processing question {i+1}/{num_questions} ({question_id})")
            
        context_data = context_per_question.get(question_id)
        if not context_data or not context_data.get("context"):
            logger.warning(f"SynthesizerNode: No context found for question {question_id}, skipping synthesis")
            continue
            
        try:
            # 3. Generate section content
            logger.info(f"SynthesizerNode: Generating content for {question_id}...")
            
            section_content = generate_section(
                question_text=question_text,
                context=context_data["context"],
                sources=context_data["sources"],
                llm_client=llm_client
            )
            logger.info(f"SynthesizerNode: Successfully generated content for {question_id} ({len(section_content)} chars)")
            
            # 4. Extract metadata
            metadata = extract_metadata(section_content, context_data["sources"])
            
            # 5. Save to database
            reuse_info = reused_sections.get(question_id)
            create_research_section(
                session=session,
                session_id=research_session.id,
                question_id=str(question_id),
                question_text=question_text,
                section_content=section_content,
                context_data=context_data,
                section_metadata=metadata,
                reuse_info=reuse_info
            )
            
            # 6. Store in state
            sections[question_id] = {
                "content": section_content,
                "sources": context_data["sources"],
                "metadata": metadata
            }
            
        except Exception as e:
            logger.error(f"Error synthesizing section for question {question_id}: {e}")
            # We don't want to fail the entire workflow if one section fails
            # but we should probably record the failure in the state if needed.

    # Update and return state
    new_state = state.copy()
    new_state.update({
        "sections": sections,
        "current_phase": ResearchPhase.EVALUATION.value,
    })
    
    logger.info(f"SynthesizerNode: Finished generating {len(sections)} sections. Phase set to {new_state['current_phase']}")
    
    return new_state
