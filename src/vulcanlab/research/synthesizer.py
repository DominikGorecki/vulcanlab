"""
Section Synthesis and Quality Evaluation Module for Deep Research.

This module provides functions to:
- Generate research section content from assembled context using LLM
- Extract metadata (word count, citation count, source diversity)
- Evaluate quality metrics (citation coverage, coherence, completeness)
- Validate citations against sources
"""

import re
import logging
from typing import List, Dict, Any, Optional
from langchain_core.prompts import PromptTemplate as LCPromptTemplate

from ..data.template_loader import load_template

logger = logging.getLogger(__name__)

# Pattern for inline citations like [Author Year, pp. X-Y] or [WorkTitle Year]
# This pattern matches anything inside square brackets, which is a broad but 
# reasonable approximation for MVP, allowing flexibility in citation formats.
CITATION_PATTERN = r'\[([^\]]+)\]'

def generate_section(
    question_text: str,
    context: str,
    sources: List[Dict[str, Any]],
    llm_client: Any,
    prompt_template: Optional[LCPromptTemplate] = None
) -> str:
    """
    Calls LLM to synthesize research section content from context.

    Args:
        question_text: The research sub-question being answered.
        context: Assembled and deduplicated context from research items.
        sources: List of source attribution dicts for the context.
        llm_client: LLM client instance (expected to have a .generate(prompt) method).
        prompt_template: Optional custom LangChain PromptTemplate. If None, loads from database.

    Returns:
        Generated section content (markdown string with inline citations).
    """
    if prompt_template is None:
        prompt_template = load_template("section_synthesis", fallback_builder=None)

    # Format sources list
    sources_list = format_sources_list(sources)

    # Format prompt with LangChain template
    prompt = prompt_template.format(
        question_text=question_text,
        context=context,
        sources_list=sources_list
    )

    try:
        # Assuming the LLM client interface similar to research_planner.py
        response = llm_client.generate(prompt)
        return response
    except Exception as e:
        logger.error(f"Error generating research section: {e}")
        raise ValueError(f"Failed to generate section: {e}")

def extract_metadata(section_content: str, sources: List[Dict[str, Any]]) -> Dict[str, Any]:
    """
    Extracts metadata from generated section content.
    
    Calculates word count, citation count, and source diversity.
    
    Args:
        section_content: The markdown content of the generated section.
        sources: List of source attribution dicts.
        
    Returns:
        Dict: {word_count: int, citation_count: int, source_diversity: int}
    """
    if not section_content:
        return {"word_count": 0, "citation_count": 0, "source_diversity": 0}

    # Word count
    words = section_content.split()
    word_count = len(words)
    
    # Citation count
    citations = re.findall(CITATION_PATTERN, section_content)
    citation_count = len(citations)
    
    # Source diversity (unique works cited)
    unique_works_cited = set()
    for i, source in enumerate(sources):
        work_id = source.get("work_id")
        work_title = source.get("work_title")
        authors = source.get("authors")
        item_id = source.get("item_id")
        
        # Build list of strings that represent this source in citations
        potential_matches = []
        if work_title:
            potential_matches.append(work_title.lower())
        if authors:
            # Match first author's last name (simple heuristic)
            first_author = authors.split(',')[0].split()[-1]
            potential_matches.append(first_author.lower())
        
        if source.get("type") == "research_result":
            potential_matches.append(f"research result {item_id or i+1}".lower())
            potential_matches.append(f"result {item_id or i+1}".lower())
            
        # Also allow matching by index like [S1] or [1]
        potential_matches.append(f"s{i+1}")
        potential_matches.append(f"{i+1}")
        
        # Check if any of these match any citation string
        source_found = False
        for citation in citations:
            citation_lower = citation.lower()
            for match in potential_matches:
                if match in citation_lower:
                    unique_works_cited.add(work_id or f"item_{item_id or i+1}")
                    source_found = True
                    break
            if source_found:
                break
                
    # If no work titles matched, but we have citations, we might want to return 
    # at least something if it's clear it's a valid citation.
    # But for now, we follow the heuristic of matching against known sources.
    
    return {
        "word_count": word_count,
        "citation_count": citation_count,
        "source_diversity": len(unique_works_cited)
    }

def evaluate_quality(
    section_content: str, 
    sources: List[Dict[str, Any]], 
    metadata: Dict[str, Any]
) -> Dict[str, Any]:
    """
    Calculates quality metrics for the generated section.
    
    Args:
        section_content: Generated markdown content.
        sources: List of source attribution dicts.
        metadata: Metadata from extract_metadata.
        
    Returns:
        Dict: {citation_coverage: float, source_diversity: int, 
               coherence_score: str, completeness_score: str}
    """
    # Citation coverage heuristic: citation_count / sentence_count
    # Sentences are approximated by counting periods followed by space/newline.
    sentences = re.split(r'\.[\s\n]+', section_content)
    sentence_count = max(1, len([s for s in sentences if s.strip()]))
    
    citation_count = metadata.get("citation_count", 0)
    citation_coverage = min(1.0, citation_count / sentence_count)
    
    source_diversity = metadata.get("source_diversity", 0)
    
    # Coherence score: simple heuristic
    # High: word count > 800 and citation coverage > 0.5
    # Medium: word count > 400 and citation coverage > 0.3
    # Low: otherwise
    word_count = metadata.get("word_count", 0)
    
    if word_count > 800 and citation_coverage > 0.5:
        coherence_score = "High"
    elif word_count > 400 and citation_coverage > 0.3:
        coherence_score = "Medium"
    else:
        coherence_score = "Low"
        
    # Completeness score heuristic: based on source diversity and word count
    if source_diversity >= 3 and word_count > 600:
        completeness_score = "High"
    elif source_diversity >= 1 and word_count > 200:
        completeness_score = "Medium"
    else:
        completeness_score = "Low"
        
    return {
        "citation_coverage": round(citation_coverage, 2),
        "source_diversity": source_diversity,
        "coherence_score": coherence_score,
        "completeness_score": completeness_score
    }

def check_citation_coverage(section_content: str, sources: List[Dict[str, Any]]) -> List[str]:
    """
    Validates all citations in the content against the provided sources.
    
    Args:
        section_content: Generated markdown content.
        sources: List of source attribution dicts.
        
    Returns:
        List of broken citations (citation strings that don't match any source).
    """
    citations = re.findall(CITATION_PATTERN, section_content)
    broken_citations = []
    
    # Build list of potential matches (titles, authors, or result placeholders)
    match_keys = []
    for i, s in enumerate(sources):
        if s.get("work_title"):
            match_keys.append(s["work_title"].lower())
        
        if s.get("authors"):
            # Match first author's last name
            first_author = s["authors"].split(',')[0].split()[-1]
            match_keys.append(first_author.lower())
        
        if s.get("type") == "research_result":
            # Must match the titles generated in _format_generation_prompt
            match_keys.append(f"research result {s.get('item_id') or i+1}".lower())
            match_keys.append(f"result {s.get('item_id') or i+1}".lower())
        
        # Also allow matching by index like [S1] or [1] if LLM defaults to that
        match_keys.append(f"s{i+1}")
        match_keys.append(f"{i+1}")
    
    for citation in citations:
        found = False
        citation_lower = citation.lower()
        for key in match_keys:
            if key in citation_lower:
                found = True
                break
        
        if not found:
            broken_citations.append(citation)
            
    return broken_citations

def format_sources_list(sources: List[Dict[str, Any]]) -> str:
    """
    Format sources list for template variable substitution.

    Args:
        sources: List of source attribution dicts.

    Returns:
        Formatted string of sources, one per line.
    """
    sources_list = []
    for i, s in enumerate(sources):
        # For research_result items, use a clearer title for attribution
        if s.get("type") == "research_result":
            title = s.get("work_title") or f"Previous Research Result {s.get('item_id') or i+1}"
        else:
            title = s.get("work_title") or "Unknown Source"

        item_type = s.get("type", "unknown")
        sources_list.append(f"{i+1}. {title} (Type: {item_type})")

    return "\n".join(sources_list)
