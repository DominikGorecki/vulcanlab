"""
Derived Output Compilation Module for generating structured summaries from summary nodes.
"""

import logging
import json
from typing import List, Optional, Dict, Any
from sqlalchemy.orm import Session, joinedload
from sqlalchemy import select

from vulcanlab.data.models.summary_node import SummaryNode
from vulcanlab.data.models.work_summary import WorkSummary, WorkSummaryType
from vulcanlab.data.models.chunk import Chunk
from vulcanlab.data.models.work import Work
from vulcanlab.summarize.llm_summarize import get_active_template, call_llm, get_llm_model

logger = logging.getLogger(__name__)


def load_summary_nodes(work_id: int, session: Session) -> List[SummaryNode]:
    """
    Query all summary_nodes for a work, ordered by start_line.
    Joins with chunks to get heading information.
    """
    stmt = (
        select(SummaryNode)
        .options(joinedload(SummaryNode.chunk))
        .where(SummaryNode.work_id == work_id)
        .order_by(SummaryNode.start_line)
    )
    result = session.execute(stmt)
    return list(result.scalars().all())


def compile_abstract(nodes: List[SummaryNode], work_title: str, session: Session) -> WorkSummary:
    """
    Synthesize a work-level abstract from all summary node gists using LLM.
    """
    if not nodes:
        raise ValueError("Cannot compile abstract: No summary nodes provided.")

    # Collect all gists
    gists = [f"- {node.gist}" for node in nodes]
    gists_text = "\n".join(gists)

    # Load template
    template_content = get_active_template("synthesize_abstract", session)
    
    # Format template
    prompt = template_content.format(
        work_title=work_title,
        gists=gists_text
    )

    # Call LLM
    model = get_llm_model()
    response_text, _ = call_llm(prompt, model)
    
    # Simple parsing - abstract is usually just text, but we might want to strip markdown
    abstract_content = response_text.strip()
    if abstract_content.startswith("```"):
        # If LLM wrapped it in markdown, try to extract
        lines = abstract_content.splitlines()
        if lines[0].startswith("```"):
            lines = lines[1:]
        if lines[-1].startswith("```"):
            lines = lines[:-1]
        abstract_content = "\n".join(lines).strip()

    # Aggregate line references from all contributing nodes
    line_references = []
    if nodes:
        min_line = min(n.start_line for n in nodes)
        max_line = max(n.end_line for n in nodes)
        line_references = [{"start_line": min_line, "end_line": max_line}]

    return WorkSummary(
        work_id=nodes[0].work_id,
        type=WorkSummaryType.ABSTRACT,
        content={"abstract": abstract_content},
        line_references=line_references
    )


def compile_outline(nodes: List[SummaryNode], session: Session) -> WorkSummary:
    """
    Build a hierarchical outline from summary nodes using heading levels.
    """
    if not nodes:
        raise ValueError("Cannot compile outline: No summary nodes provided.")

    outline_items = []
    for node in nodes:
        # Get heading and level from chunk
        chunk = node.chunk
        heading = ""
        depth = 1
        
        if chunk and chunk.heading_breadcrumbs:
            breadcrumbs = chunk.heading_breadcrumbs.split(" > ")
            heading = breadcrumbs[-1]
            depth = len(breadcrumbs)
        elif chunk:
            heading = chunk.content.splitlines()[0].lstrip('#').strip() if chunk.content.startswith('#') else "Untitled Section"
            if chunk.level.startswith('H'):
                try:
                    depth = int(chunk.level[1:])
                except ValueError:
                    depth = 1

        outline_items.append({
            "heading": heading,
            "gist": node.gist,
            "depth": depth,
            "start_line": node.start_line,
            "end_line": node.end_line
        })

    # Optional: build nested structure if needed, but for now a flat list with depth is often enough for JSONB
    # The requirement says "Build nested children structure"
    
    def build_hierarchy(items: List[dict]) -> List[dict]:
        root = []
        stack = [] # (depth, children_list)
        
        for item in items:
            depth = item["depth"]
            node = {
                "heading": item["heading"],
                "gist": item["gist"],
                "start_line": item["start_line"],
                "end_line": item["end_line"],
                "children": []
            }
            
            while stack and stack[-1][0] >= depth:
                stack.pop()
            
            if not stack:
                root.append(node)
            else:
                stack[-1][1].append(node)
                
            stack.append((depth, node["children"]))
            
        return root

    nested_outline = build_hierarchy(outline_items)

    # Aggregate line references
    min_line = min(n.start_line for n in nodes)
    max_line = max(n.end_line for n in nodes)
    line_references = [{"start_line": min_line, "end_line": max_line}]

    return WorkSummary(
        work_id=nodes[0].work_id,
        type=WorkSummaryType.OUTLINE,
        content={"outline": nested_outline},
        line_references=line_references
    )


def compile_key_concepts(nodes: List[SummaryNode], work_title: str, session: Session) -> WorkSummary:
    """
    Aggregate and deduplicate definitions/key_terms across nodes, then clean up with LLM.
    """
    if not nodes:
        raise ValueError("Cannot compile key concepts: No summary nodes provided.")

    # 1. Aggregate and deduplicate
    concepts_map = {} # term_name -> {definition: str, occurrences: List[dict]}

    for node in nodes:
        # Process definitions
        for d in node.definitions:
            term = d["term"].strip().lower()
            if term not in concepts_map:
                concepts_map[term] = {"term": d["term"], "definition": d["definition"], "occurrences": []}
            
            # Use longest definition if multiple exist
            if len(d["definition"]) > len(concepts_map[term]["definition"]):
                 concepts_map[term]["definition"] = d["definition"]
                 
            concepts_map[term]["occurrences"].append({
                "start_line": d["start_line"],
                "end_line": d["end_line"]
            })

        # Process key terms
        for kt in node.key_terms:
            term = kt["term"].strip().lower()
            if term not in concepts_map:
                concepts_map[term] = {"term": kt["term"], "definition": "", "occurrences": []}
            
            concepts_map[term]["occurrences"].append({
                "start_line": kt["start_line"],
                "end_line": kt["end_line"]
            })

    # 2. Prepare for LLM synthesis
    concepts_list = []
    for term_data in concepts_map.values():
        concepts_list.append({
            "term": term_data["term"],
            "definition": term_data["definition"]
        })

    # Load template
    template_content = get_active_template("organize_key_concepts", session)
    
    # Format template
    prompt = template_content.format(
        work_title=work_title,
        concepts=json.dumps(concepts_list, indent=2)
    )

    # Call LLM
    model = get_llm_model()
    response_text, _ = call_llm(prompt, model)
    
    # Parse LLM response (expected to be JSON)
    try:
        json_str = response_text
        if "```json" in response_text:
            json_str = response_text.split("```json")[1].split("```")[0].strip()
        elif "```" in response_text:
            json_str = response_text.split("```")[1].split("```")[0].strip()
        
        refined_concepts = json.loads(json_str)
        # Ensure it's a list
        if isinstance(refined_concepts, dict) and "key_concepts" in refined_concepts:
            refined_concepts = refined_concepts["key_concepts"]
        elif not isinstance(refined_concepts, list):
            refined_concepts = []
            
        # Re-attach occurrences to refined concepts
        for concept in refined_concepts:
            term_key = concept.get("term", "").strip().lower()
            if term_key in concepts_map:
                concept["occurrences"] = concepts_map[term_key]["occurrences"]
            else:
                concept["occurrences"] = []
                
    except (json.JSONDecodeError, KeyError, TypeError) as e:
        logger.error(f"Failed to parse LLM response for key concepts: {e}")
        # Fallback to deduplicated list if LLM fails
        refined_concepts = []
        for term_data in concepts_map.values():
            refined_concepts.append({
                "term": term_data["term"],
                "definition": term_data["definition"],
                "occurrences": term_data["occurrences"]
            })

    # Aggregate line references
    all_refs = []
    for c in refined_concepts:
        all_refs.extend(c.get("occurrences", []))
    
    # Simplify line references for the summary record
    if all_refs:
        min_line = min(r["start_line"] for r in all_refs)
        max_line = max(r["end_line"] for r in all_refs)
        line_references = [{"start_line": min_line, "end_line": max_line}]
    else:
        line_references = []

    return WorkSummary(
        work_id=nodes[0].work_id,
        type=WorkSummaryType.KEY_CONCEPTS,
        content={"key_concepts": refined_concepts},
        line_references=line_references
    )


def compile_chapter_summaries(nodes: List[SummaryNode], session: Session) -> WorkSummary:
    """
    Extract summaries for H1 and H2 level sections.
    """
    if not nodes:
        raise ValueError("Cannot compile chapter summaries: No summary nodes provided.")

    chapters = []
    for node in nodes:
        chunk = node.chunk
        if chunk and chunk.level in ("H1", "H2"):
            heading = ""
            if chunk.heading_breadcrumbs:
                heading = chunk.heading_breadcrumbs.split(" > ")[-1]
            else:
                heading = chunk.content.splitlines()[0].lstrip('#').strip() if chunk.content.startswith('#') else "Untitled"

            chapters.append({
                "heading": heading,
                "level": chunk.level,
                "summary": node.gist,
                "line_references": [{"start_line": node.start_line, "end_line": node.end_line}]
            })

    # Aggregate line references
    if chapters:
        min_line = min(n.start_line for n in nodes if n.chunk and n.chunk.level in ("H1", "H2"))
        max_line = max(n.end_line for n in nodes if n.chunk and n.chunk.level in ("H1", "H2"))
        line_references = [{"start_line": min_line, "end_line": max_line}]
    else:
        line_references = []

    return WorkSummary(
        work_id=nodes[0].work_id,
        type=WorkSummaryType.CHAPTER_SUMMARIES,
        content={"chapters": chapters},
        line_references=line_references
    )


def generate_derived_output(work_id: int, output_type: str, session: Session) -> WorkSummary:
    """
    Route to appropriate compile function and handle storage (upsert).
    """
    logger.info(f"Generating {output_type} for work {work_id}")
    
    # 1. Load work and nodes
    work = session.get(Work, work_id)
    if not work:
        raise ValueError(f"Work with id {work_id} not found.")

    nodes = load_summary_nodes(work_id, session)
    if not nodes:
        raise ValueError(f"No summary nodes found for work {work_id}.")

    # 2. Route to compiler
    if output_type == WorkSummaryType.ABSTRACT:
        new_summary = compile_abstract(nodes, work.title, session)
    elif output_type == WorkSummaryType.OUTLINE:
        new_summary = compile_outline(nodes, session)
    elif output_type == WorkSummaryType.KEY_CONCEPTS:
        new_summary = compile_key_concepts(nodes, work.title, session)
    elif output_type == WorkSummaryType.CHAPTER_SUMMARIES:
        new_summary = compile_chapter_summaries(nodes, session)
    else:
        raise ValueError(f"Invalid output type: {output_type}")

    # 3. Upsert
    stmt = select(WorkSummary).where(
        WorkSummary.work_id == work_id,
        WorkSummary.type == output_type
    )
    existing = session.execute(stmt).scalar_one_or_none()
    
    logger.info(f"Derived output {output_type} completed for work {work_id}")
    
    if existing:
        existing.content = new_summary.content
        existing.line_references = new_summary.line_references
        return existing
    else:
        session.add(new_summary)
        return new_summary


def get_derived_outputs(work_id: int, session: Session) -> List[WorkSummary]:
    """
    Query all work_summaries for a work.
    """
    stmt = select(WorkSummary).where(WorkSummary.work_id == work_id)
    result = session.execute(stmt)
    return list(result.scalars().all())
