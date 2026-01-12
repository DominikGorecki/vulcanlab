"""
Research Planner node for LangGraph workflow.

Analyzes the collection, generates a research plan using LLM,
and persists it to the state and database.
"""

import logging
from typing import Any, Dict

from sqlalchemy.orm import Session

from ..research_planner import analyze_collection, generate_research_plan
from ..state import ResearchState
from ...ai import create_langchain_chat, ModelTier
from ...data.research_session import update_research_session, get_research_session_by_thread_id
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


def ResearchPlannerNode(state: ResearchState, session: Session) -> ResearchState:
    """
    LangGraph node to analyze collection and generate research plan.
    
    Args:
        state: Current ResearchState.
        session: Database session.
        
    Returns:
        Updated ResearchState.
    """
    collection_id = state.get("collection_id")
    thread_id = state.get("thread_id")
    
    if not collection_id:
        raise ValueError("collection_id missing from state")
    if not thread_id:
        raise ValueError("thread_id missing from state")
        
    logger.info(f"ResearchPlannerNode: Analyzing collection {collection_id} for thread {thread_id}")
    
    # 1. Analyze collection
    collection_data = analyze_collection(collection_id, session)
    
    # 2. Get LLM client (FULL tier for planning with 2-minute timeout)
    chat_stack = create_langchain_chat(tier=ModelTier.FULL, request_timeout=120)
    llm_client = LLMClientWrapper(chat_stack.chat)
    
    # 3. Generate research plan
    plan = generate_research_plan(collection_data, llm_client)
    
    # 4. Extract item notes for state
    item_notes = [
        {"item_id": item["id"], "note": item["note"], "type": item["type"]}
        for item in collection_data.get("items", [])
    ]
    
    # 5. Update research session in database
    research_session = get_research_session_by_thread_id(session, thread_id)
    if not research_session:
        raise ValueError(f"Research session with thread_id {thread_id} not found")
        
    update_research_session(
        session,
        research_session.id,
        {
            "research_plan": plan,
            "current_phase": ResearchPhase.RESEARCH,
        }
    )
    
    # 6. Update and return state
    new_state = state.copy()
    new_state.update({
        "research_plan": plan,
        "current_phase": ResearchPhase.RESEARCH.value,
        "item_notes": item_notes,
        "collection_description": collection_data.get("description", "") or "",
    })
    
    return new_state
