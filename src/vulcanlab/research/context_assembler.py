"""
Context Assembly Module for Deep Research.

This module handles fetching, consolidating, and deduplicating collection items
to provide context for research sub-questions.
"""

import re
from typing import List, Dict, Any, Optional, Tuple
import tiktoken
from sqlalchemy import select, and_
from sqlalchemy.orm import Session

from ..data.models.collection_item import CollectionItem
from ..data.models.enums import CollectionItemType
from ..data.models.work import Work
from ..data.models.chunk import Chunk
from ..data.models.query import Query
from ..data.models.result import Result

# Re-defining patterns here for independence or importing from collections
# Since collections is a core module, it's fine to import from it.
# However, to avoid any circular dependency issues and keep it clean, 
# we'll use the patterns directly or import them.
from ..collections import (
    EXCERPT_PATTERN,
    RESEARCH_RESULT_PATTERN,
    RESEARCH_QUERY_PATTERN
)

def fetch_collection_items(item_ids: List[int], session: Session) -> List[Dict[str, Any]]:
    """
    Retrieves excerpts, results, and queries for the given collection item IDs.
    
    Args:
        item_ids: List of CollectionItem IDs to fetch.
        session: Database session.
        
    Returns:
        List of dicts: [{item_id, type, content, work_metadata, preview}]
    """
    if not item_ids:
        return []

    # Fetch CollectionItems
    items_query = select(CollectionItem).where(CollectionItem.id.in_(item_ids))
    collection_items = session.execute(items_query).scalars().all()
    
    # Sort them in the order they were requested to maintain any prioritization
    # or just use the order from the database if preferred.
    # The ticket mentions prioritization by type later in assemble_context_for_question.
    
    results = []
    for item in collection_items:
        item_data = {
            "item_id": item.id,
            "type": item.item_type.value if hasattr(item.item_type, 'value') else item.item_type,
            "content": "",
            "work_metadata": None,
            "preview": item.note or ""
        }
        
        if item.item_type == CollectionItemType.EXCERPT:
            match = re.match(EXCERPT_PATTERN, item.link)
            if match:
                work_id, start_line, end_line = map(int, match.groups())
                item_data["start_line"] = start_line
                item_data["end_line"] = end_line
                
                work = session.get(Work, work_id)
                if work:
                    item_data["work_metadata"] = {
                        "work_id": work.id,
                        "title": work.title,
                        "authors": work.authors,
                        "year": work.year
                    }
                    
                    # Fetch chunks between start and end (inclusive)
                    chunks_query = select(Chunk).where(
                        and_(
                            Chunk.work_id == work_id,
                            Chunk.start_line >= start_line,
                            Chunk.end_line <= end_line
                        )
                    ).order_by(Chunk.start_line.asc())
                    
                    chunks = session.execute(chunks_query).scalars().all()
                    if chunks:
                        item_data["content"] = "\n\n".join([c.content for c in chunks])
                        item_data["heading_breadcrumbs"] = chunks[0].heading_breadcrumbs
                        item_data["preview"] = item_data["content"][:2000]
                    else:
                        # Fallback if no chunks found in range
                        item_data["content"] = "Excerpt content not found."
                else:
                    item_data["content"] = "Source work deleted."
                    
        elif item.item_type == CollectionItemType.RESEARCH_RESULT:
            match = re.match(RESEARCH_RESULT_PATTERN, item.link)
            if match:
                query_id, result_id = map(int, match.groups())
                result_rec = session.get(Result, result_id)
                if result_rec:
                    item_data["content"] = result_rec.response_text or ""
                    item_data["preview"] = item_data["content"][:2000]
                else:
                    item_data["content"] = "Research result deleted."
                    
        elif item.item_type == CollectionItemType.RESEARCH_QUERY:
            match = re.match(RESEARCH_QUERY_PATTERN, item.link)
            if match:
                query_id = int(match.groups()[0])
                query_rec = session.get(Query, query_id)
                if query_rec:
                    item_data["content"] = query_rec.original_query
                    item_data["preview"] = item_data["content"][:2000]
                else:
                    item_data["content"] = "Research query deleted."
                    
        results.append(item_data)
        
    return results

def deduplicate_content(items: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    """
    Removes overlapping content and merges overlapping excerpts from same work.
    
    Args:
        items: List of item dicts with 'content' and 'work_metadata'.
        
    Returns:
        Deduplicated list of items.
    """
    if not items:
        return []

    # 1. Merge overlapping excerpts from the same work
    work_excerpts = {}  # work_id -> list of items
    non_excerpts = []
    
    for item in items:
        if item["type"] == "excerpt" and item["work_metadata"]:
            work_id = item["work_metadata"]["work_id"]
            if work_id not in work_excerpts:
                work_excerpts[work_id] = []
            work_excerpts[work_id].append(item)
        else:
            non_excerpts.append(item)
            
    merged_items = []
    
    for work_id, excerpts in work_excerpts.items():
        if len(excerpts) <= 1:
            merged_items.extend(excerpts)
            continue
            
        # Sort by length descending to prioritize longer content
        excerpts.sort(key=lambda x: len(x["content"]), reverse=True)
        
        unique_excerpts = []
        for current in excerpts:
            content = current["content"]
            if not content:
                continue
                
            is_redundant = False
            for unique in unique_excerpts:
                # If current is already contained in a longer one, skip it
                if content in unique["content"]:
                    is_redundant = True
                    break
                
                # Check for 80% overlap
                # For MVP, we use a simple heuristic: if a large chunk of current is in unique
                if len(content) > 100:
                    if content[:int(len(content)*0.8)] in unique["content"]:
                        is_redundant = True
                        break
            
            if not is_redundant:
                unique_excerpts.append(current)
        
        merged_items.extend(unique_excerpts)
        
    # 2. General deduplication for all items (including research_results)
    final_items = []
    all_potential_items = non_excerpts + merged_items
    
    # Sort by length descending
    all_potential_items.sort(key=lambda x: len(x.get("content", "")), reverse=True)
    
    for item in all_potential_items:
        content = item.get("content", "")
        if not content:
            continue
            
        is_redundant = False
        for existing in final_items:
            existing_content = existing.get("content", "")
            if content in existing_content:
                is_redundant = True
                break
            
            if len(content) > 100:
                if content[:int(len(content)*0.8)] in existing_content:
                    is_redundant = True
                    break
        
        if not is_redundant:
            final_items.append(item)
            
    return final_items

def apply_token_limit(content: str, max_tokens: int = 35000) -> Tuple[str, int]:
    """
    Truncates content to token budget using tiktoken.
    
    Args:
        content: The content string to truncate.
        max_tokens: Maximum number of tokens allowed.
        
    Returns:
        Tuple of (truncated_content, token_count).
    """
    try:
        enc = tiktoken.encoding_for_model("gpt-4")
    except Exception:
        # Fallback to cl100k_base if model not found
        enc = tiktoken.get_encoding("cl100k_base")
        
    tokens = enc.encode(content)
    token_count = len(tokens)
    
    if token_count > max_tokens:
        truncated_tokens = tokens[:max_tokens]
        truncated_content = enc.decode(truncated_tokens) + "\n\n...[truncated]"
        return truncated_content, max_tokens
        
    return content, token_count

def build_source_attribution(items: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    """
    Creates source metadata list for attribution.
    
    Args:
        items: List of item dicts.
        
    Returns:
        List of source attribution dicts.
    """
    sources = []
    for item in items:
        source = {
            "item_id": item["item_id"],
            "type": item["type"],
            "work_id": item["work_metadata"]["work_id"] if item.get("work_metadata") else None,
            "work_title": item["work_metadata"]["title"] if item.get("work_metadata") else None,
            "authors": item["work_metadata"]["authors"] if item.get("work_metadata") else None,
            "preview": item["content"][:2000] if item.get("content") else ""
        }
        sources.append(source)
    return sources

def assemble_context_for_question(
    question_id: int,
    relevant_item_ids: List[int],
    reuse_info: Optional[Dict[str, Any]] = None,
    session: Optional[Session] = None
) -> Dict[str, Any]:
    """
    Main assembly logic to consolidate context for a sub-question.
    
    Args:
        question_id: ID of the sub-question.
        relevant_item_ids: List of CollectionItem IDs relevant to the question.
        reuse_info: Optional reuse strategy info from result matching.
        session: Database session.
        
    Returns:
        Dict: {context: str, token_count: int, sources: list}
    """
    if session is None:
        raise ValueError("Database session is required for context assembly.")

    context_parts = []
    sources = []
    
    if reuse_info and reuse_info.get("source_result_ids"):
        # Reuse workflow: fetch existing research results
        source_result_ids = reuse_info["source_result_ids"]
        
        # We need to find the collection items that correspond to these results
        # or just fetch the results directly. The ticket says:
        # "Fetch reused research_result items by IDs in reuse_info['source_result_ids']"
        # but source_result_ids are likely Result IDs, not CollectionItem IDs.
        # Actually, let's fetch the Results directly.
        
        results_query = select(Result).where(Result.id.in_(source_result_ids))
        results = session.execute(results_query).scalars().all()
        
        for res in results:
            context_parts.append(res.response_text or "")
            sources.append({
                "item_id": None,
                "type": "research_result",
                "work_id": None,
                "work_title": None,
                "preview": (res.response_text or "")[:2000]
            })
    else:
        # New generation workflow
        items = fetch_collection_items(relevant_item_ids, session)
        
        # Prioritize by type: research_result > excerpt > research_query
        type_priority = {
            "research_result": 0,
            "excerpt": 1,
            "research_query": 2
        }
        items.sort(key=lambda x: type_priority.get(x["type"], 99))
        
        # Deduplicate
        items = deduplicate_content(items)
        
        for item in items:
            header = f"--- Source: {item['type'].upper()}"
            if item.get("work_metadata"):
                wm = item["work_metadata"]
                header += f" | {wm['title']} ({wm['authors']}, {wm['year']})"
            header += " ---\n"
            
            context_parts.append(header + item["content"])
            
        sources = build_source_attribution(items)
        
    full_context = "\n\n".join(context_parts)
    
    # Apply token limit (35K)
    final_context, token_count = apply_token_limit(full_context, max_tokens=35000)
    
    return {
        "context": final_context,
        "token_count": token_count,
        "sources": sources
    }
