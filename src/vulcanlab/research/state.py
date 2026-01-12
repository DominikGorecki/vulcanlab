from typing import TypedDict, Optional, List, Dict, Any

class ResearchState(TypedDict):
    """
    ResearchState schema for LangGraph workflow state management.
    
    This state is persisted across nodes in the research workflow.
    """
    collection_id: int
    collection_description: str
    item_notes: List[Dict[str, Any]]  # list of {item_id, note, type}
    research_plan: Dict[str, Any]  # {outline, sub_questions, token_budgets}
    current_phase: str
    sections: Dict[str, Dict[str, Any]]  # {question: {content, sources, quality}}
    context_per_question: Dict[str, Any]
    reused_sections: Dict[str, Dict[str, Any]]  # {question_id: {source_result_id, reuse_type, similarity}}
    available_results: List[Dict[str, Any]]  # Cache of research_result items
    synthesis: str
    quality_metrics: Dict[str, Any]
    refinement_needed: List[str]
    refinement_iteration_count: int
    thread_id: str
