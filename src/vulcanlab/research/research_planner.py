"""
Research planning logic for generating structured research plans from collections.

This module provides functions to:
- Analyze collection metadata and items
- Generate research plans using LLM
- Validate research plan structure

Used by both manual wizard (Step 1) and automated LangGraph planning node.
"""

import re
from typing import TypedDict, Optional, Any
from sqlalchemy.orm import Session
from sqlalchemy import select, func
from langchain_core.prompts import PromptTemplate as LCPromptTemplate

import logging
logger = logging.getLogger(__name__)

from ..data.models.collection import Collection
from ..data.models.collection_item import CollectionItem
from ..data.models.enums import CollectionItemType
from ..data.models.result import Result
from ..data.models.work import Work
from ..data.models.chunk import Chunk
from ..data.template_loader import load_template
from ..utils.json_utils import extract_json


class SubQuestion(TypedDict):
    """
    Sub-question within a research plan.

    Attributes:
        id: Unique identifier for the sub-question (e.g., "sq1", "sq2").
        question: The research question text.
        rationale: Explanation of why this question is important.
        estimated_tokens: Estimated token count needed to answer (20K-40K typical).
        relevant_items: List of collection item IDs relevant to this question.
    """
    id: str
    question: str
    rationale: str
    estimated_tokens: int
    relevant_items: list[int]


class ResearchPlan(TypedDict):
    """
    Structured research plan generated from collection analysis.

    Attributes:
        research_goal: Overall goal of the research.
        key_themes: List of main themes identified in the collection.
        sub_questions: List of sub-questions to answer.
        synthesis_approach: Strategy for synthesizing answers into final report.
    """
    research_goal: str
    key_themes: list[str]
    sub_questions: list[SubQuestion]
    synthesis_approach: str


def analyze_collection(collection_id: int, session: Session) -> dict[str, Any]:
    """
    Analyze a collection and return structured metadata for research planning.

    Fetches collection metadata (name, description, tags) and item summaries
    (types, notes, counts). For research_result items, includes preview text.
    For excerpt items, includes work metadata.

    Args:
        collection_id: ID of the collection to analyze.
        session: Database session.

    Returns:
        Dictionary with collection metadata and item summaries:
        {
            "collection_id": int,
            "name": str,
            "description": str | None,
            "tags": list[str],
            "item_count": int,
            "items_by_type": {
                "excerpt": int,
                "research_result": int,
                "research_query": int
            },
            "items": [
                {
                    "id": int,
                    "type": str,
                    "link": str,
                    "note": str | None,
                    "preview": str | None,  # For research_result items
                    "metadata": dict        # For excerpt items (title, authors, year)
                }
            ]
        }

    Raises:
        ValueError: If collection not found.
    """
    # Fetch collection
    collection = session.get(Collection, collection_id)
    if not collection:
        raise ValueError(f"Collection {collection_id} not found")

    # Count items by type
    items_by_type = {
        "excerpt": 0,
        "research_result": 0,
        "research_query": 0
    }

    query = select(CollectionItem.item_type, func.count(CollectionItem.id)).where(
        CollectionItem.collection_id == collection_id
    ).group_by(CollectionItem.item_type)

    for item_type, count in session.execute(query).all():
        items_by_type[item_type.value] = count

    # Fetch all items with details
    items_query = select(CollectionItem).where(
        CollectionItem.collection_id == collection_id
    ).order_by(CollectionItem.order)

    items = []
    for item in session.execute(items_query).scalars().all():
        item_data = {
            "id": item.id,
            "type": item.item_type.value,
            "link": item.link,
            "note": item.note,
            "preview": None,
            "metadata": {}
        }

        # For research_result items, add preview (approx 350 words / 2000 chars)
        if item.item_type == CollectionItemType.RESEARCH_RESULT:
            # Parse result_id from link: /rag/{query_id}/results/{result_id}
            match = re.search(r"/results/(\d+)", item.link)
            if match:
                result_id = int(match.group(1))
                result = session.get(Result, result_id)
                if result:
                    item_data["preview"] = result.response_text[:2000] + "..." if len(result.response_text) > 2000 else result.response_text

        # For excerpt items, add work metadata (title, authors, year) and content preview
        elif item.item_type == CollectionItemType.EXCERPT:
            # Parse work_id from link: /search/result/{query_id}/{work_id}/{chunk_id}
            # or the new format: /search/result/{work_id}/{start_line}/{end_line}
            match = re.search(r"/search/result/\d+/(\d+)", item.link)
            if match:
                try:
                    work_id = int(match.group(1))
                    work = session.get(Work, work_id)
                    if work:
                        item_data["metadata"] = {
                            "title": work.title,
                            "authors": work.authors,
                            "year": work.year
                        }
                    
                    # Fetch actual excerpt content for planning context
                    # The link format might vary, but we often have /search/result/{query_id}/{work_id}/{chunk_id}
                    # or similar. If we can't find specific start/end from link, we'll try to find chunks.
                    # Based on src/vulcanlab/collections/__init__.py: EXCERPT_PATTERN = r'^/search/result/(\d+)/(\d+)/(\d+)$'
                    # which is query_id, work_id, start_line (or chunk_id depending on how it's used).
                    
                    excerpt_match = re.match(r'^/search/result/(\d+)/(\d+)/(\d+)$', item.link)
                    if excerpt_match:
                        _, w_id, start_val = map(int, excerpt_match.groups())
                        # If start_val is a chunk ID or line number, we'll try to get content
                        # For simplicity and to match context_assembler logic:
                        chunks_query = select(Chunk).where(
                            (Chunk.work_id == w_id) & 
                            (Chunk.start_line >= start_val)
                        ).order_by(Chunk.start_line.asc()).limit(5) # Get a few chunks for context
                        
                        chunks = session.execute(chunks_query).scalars().all()
                        if chunks:
                            full_text = "\n\n".join([c.content for c in chunks])
                            item_data["preview"] = full_text[:2000] + "..." if len(full_text) > 2000 else full_text
                except (ValueError, IndexError):
                    pass

        items.append(item_data)

    return {
        "collection_id": collection_id,
        "name": collection.name,
        "description": collection.description,
        "tags": collection.tags if collection.tags else [],
        "item_count": len(items),
        "items_by_type": items_by_type,
        "items": items
    }


def generate_research_plan(
    collection_data: dict[str, Any],
    llm_client: Any,
    prompt_template: Optional[LCPromptTemplate] = None
) -> ResearchPlan:
    """
    Generate a structured research plan using an LLM.

    Takes collection metadata and calls LLM with a formatted prompt to generate
    a research plan with sub-questions, token budgets, and synthesis approach.

    Args:
        collection_data: Dictionary from analyze_collection().
        llm_client: LLM client instance (from vulcanlab.ai).
        prompt_template: Optional custom LangChain PromptTemplate. If None, loads from database.

    Returns:
        ResearchPlan dictionary with validated structure.

    Raises:
        ValueError: If LLM response is invalid JSON or missing required fields.
    """
    # Load template from database if not provided
    if prompt_template is None:
        prompt_template = load_template("research_planning", fallback_builder=None)

    # Prepare template variables from collection data
    template_vars = prepare_template_variables(collection_data)

    # Format prompt with LangChain template
    prompt = prompt_template.format(**template_vars)

    # Call LLM
    try:
        import json

        # Get response string
        response = llm_client.generate(prompt)
        
        # Ensure response is a string (defense in depth if wrapper fails)
        if not isinstance(response, str):
            logger.warning(f"LLM client returned non-string response type: {type(response)}")
            response = str(response)

        # Clean and extract JSON (handles markdown, double braces, and extra text)
        clean_response = extract_json(response)

        # Parse JSON response
        plan_dict = json.loads(clean_response)

        # Validate and return
        validate_research_plan(plan_dict)
        return plan_dict

    except json.JSONDecodeError as e:
        logger.error(f"LLM response failed JSON parsing. Response: {response[:500]}...")
        raise ValueError(f"LLM response is not valid JSON: {e}")
    except Exception as e:
        logger.error(f"Error in generate_research_plan: {e}")
        raise ValueError(f"Error generating research plan: {e}")


def validate_research_plan(plan_dict: dict) -> None:
    """
    Validate that a research plan dictionary has the required structure.

    Checks for required fields and validates sub-questions structure.

    Args:
        plan_dict: Dictionary to validate as ResearchPlan.

    Raises:
        ValueError: If validation fails with description of missing/invalid fields.
    """
    # Check required top-level fields
    required_fields = ["research_goal", "sub_questions"]
    for field in required_fields:
        if field not in plan_dict:
            raise ValueError(f"Missing required field: {field}")

    # Validate research_goal is non-empty string
    if not isinstance(plan_dict["research_goal"], str) or not plan_dict["research_goal"].strip():
        raise ValueError("research_goal must be a non-empty string")

    # Validate sub_questions is a list with at least 1 item
    sub_questions = plan_dict["sub_questions"]
    if not isinstance(sub_questions, list):
        raise ValueError("sub_questions must be a list")

    if len(sub_questions) == 0:
        raise ValueError("sub_questions must contain at least 1 item")

    # Validate each sub-question
    required_subq_fields = ["id", "question", "estimated_tokens", "relevant_items"]
    for i, subq in enumerate(sub_questions):
        if not isinstance(subq, dict):
            raise ValueError(f"sub_question[{i}] must be a dictionary")

        for field in required_subq_fields:
            if field not in subq:
                raise ValueError(f"sub_question[{i}] missing required field: {field}")

        # Validate estimated_tokens is a positive integer
        if not isinstance(subq["estimated_tokens"], int) or subq["estimated_tokens"] <= 0:
            raise ValueError(f"sub_question[{i}].estimated_tokens must be a positive integer")

        # Validate question is non-empty string
        if not isinstance(subq["question"], str) or not subq["question"].strip():
            raise ValueError(f"sub_question[{i}].question must be a non-empty string")


def prepare_template_variables(collection_data: dict[str, Any]) -> dict[str, Any]:
    """
    Prepare template variables from collection data for LangChain template formatting.

    Pre-formats complex structures (like items list) into strings suitable for template
    variable substitution.

    Args:
        collection_data: Dictionary from analyze_collection().

    Returns:
        Dictionary of template variables ready for LangChain PromptTemplate.format().
    """
    # Format items list
    items_list = []
    for item in collection_data["items"]:
        note_text = f" - Note: {item['note']}" if item["note"] else ""

        detail_parts = []
        if item.get("preview"):
            detail_parts.append(f"Preview: {item['preview']}")

        if item.get("metadata"):
            meta = item["metadata"]
            meta_str = f"Source: {meta.get('title', 'Unknown')}"
            if meta.get('authors'):
                meta_str += f" by {meta.get('authors')}"
            if meta.get('year'):
                meta_str += f" ({meta.get('year')})"
            detail_parts.append(meta_str)

        details = f"\n    {(' | '.join(detail_parts))}" if detail_parts else ""
        items_list.append(f"- [{item['type']}] ID={item['id']}: {item['link']}{note_text}{details}")

    return {
        "name": collection_data["name"],
        "description": collection_data["description"] or "No description",
        "tags": ", ".join(collection_data["tags"]) if collection_data["tags"] else "None",
        "item_count": collection_data["item_count"],
        "excerpt_count": collection_data["items_by_type"]["excerpt"],
        "research_result_count": collection_data["items_by_type"]["research_result"],
        "query_count": collection_data["items_by_type"]["research_query"],
        "items_list": "\n".join(items_list) if items_list else "No items"
    }
