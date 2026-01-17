"""
Prompt generation logic including token budget calculation and content pruning.
"""

from dataclasses import dataclass
from typing import List, Tuple
from sqlalchemy.orm import Session

from vulcanlab.data.models.summarize_settings import SummarizeSettings
from vulcanlab.summarization.heading_selector import HeadingInfo, select_headings_for_summarization
from vulcanlab.summarization.chunk_ranker import RankedChunk, rank_content_chunks
from vulcanlab.data.template_loader import get_active_template


@dataclass
class PromptBudget:
    """Dataclass for tracking token budget across LLM calls."""
    max_calls: int
    max_tokens_per_call: int
    tokens_per_word: float
    current_token_count: int = 0


@dataclass
class HeadingWithChunks:
    """Container for a heading and its associated ranked chunks."""
    heading: HeadingInfo
    ranked_chunks: List[RankedChunk]
    total_tokens: int = 0


@dataclass
class PromptBatch:
    """Dataclass for an assembled LLM prompt batch."""
    prompt_index: int
    content: str
    heading_ids: List[int]
    estimated_tokens: int


def estimate_tokens(text: str, tokens_per_word: float) -> int:
    """
    Estimate token count by multiplying word count by a ratio.
    """
    if not text:
        return 0
    words = text.split()
    return int(len(words) * tokens_per_word)


def get_heading_level(level_str: str) -> int:
    """
    Parse heading level string (e.g., "H1", "H2") to integer.
    """
    try:
        if level_str.startswith('H') and level_str[1:].isdigit():
            return int(level_str[1:])
    except (ValueError, IndexError):
        pass
    return 99


def calculate_heading_with_chunks_tokens(
    hc: HeadingWithChunks, 
    tokens_per_word: float
) -> int:
    """
    Calculate total tokens for a heading and its chunks.
    """
    tokens = estimate_tokens(hc.heading.heading_title, tokens_per_word)
    for rc in hc.ranked_chunks:
        tokens += estimate_tokens(rc.content, tokens_per_word)
    return tokens


def calculate_total_budget(
    headings_with_chunks: List[HeadingWithChunks], 
    settings: SummarizeSettings
) -> Tuple[int, int]:
    """
    Sum tokens across all headings and chunks.
    Returns (total_tokens, max_budget).
    """
    total = 0
    for hc in headings_with_chunks:
        hc.total_tokens = calculate_heading_with_chunks_tokens(hc, settings.tokens_per_word)
        total += hc.total_tokens
        
    max_budget = settings.max_llm_calls * settings.max_tokens_per_call
    return total, max_budget


def _total_tokens(headings_with_chunks: List[HeadingWithChunks]) -> int:
    """Helper to sum tokens from all containers."""
    return sum(hc.total_tokens for hc in headings_with_chunks)


def prune_to_budget(
    headings_with_chunks: List[HeadingWithChunks], 
    max_budget: int, 
    settings: SummarizeSettings
) -> List[HeadingWithChunks]:
    """
    Iteratively remove chunks and then headings until under max_budget.
    Prioritizes keeping H1/H2 over H3+.
    """
    # Initialize total_tokens for each heading container
    for hc in headings_with_chunks:
        hc.total_tokens = calculate_heading_with_chunks_tokens(hc, settings.tokens_per_word)

    # 1. Prune chunks while respecting minimums
    while _total_tokens(headings_with_chunks) > max_budget:
        # Find candidates for chunk removal: headings with chunks above minimum
        candidates = []
        for hc in headings_with_chunks:
            level = get_heading_level(hc.heading.level)
            min_chunks = settings.h1_h2_min_chunks if level <= 2 else settings.h3_min_chunks
            if len(hc.ranked_chunks) > min_chunks:
                candidates.append(hc)
        
        if not candidates:
            break
            
        # Select candidate: lowest level heading (highest H number)
        # then most chunks.
        target_hc = max(
            candidates,
            key=lambda hc: (get_heading_level(hc.heading.level), len(hc.ranked_chunks))
        )
        
        # Remove lowest-ranked chunk (last one in list)
        removed_chunk = target_hc.ranked_chunks.pop()
        target_hc.total_tokens -= estimate_tokens(removed_chunk.content, settings.tokens_per_word)

    # 2. If still over, remove entire headings starting from lowest level
    while _total_tokens(headings_with_chunks) > max_budget and headings_with_chunks:
        # Find lowest level heading
        target_hc = max(
            headings_with_chunks,
            key=lambda hc: (get_heading_level(hc.heading.level), hc.total_tokens)
        )
        headings_with_chunks.remove(target_hc)

    return headings_with_chunks


def format_section(heading: HeadingInfo, chunks: List[RankedChunk]) -> str:
    """
    Format a heading and its chunks for the prompt.
    """
    lines = [
        f"# {heading.heading_title}",
        f"-- id: {heading.chunk_id}",
        f"-- lines: {heading.start_line}-{heading.end_line}",
        ""
    ]

    for rc in chunks:
        lines.append(rc.content)
        lines.append(f"-- chunk_id: {rc.chunk_id}, lines: {rc.start_line}-{rc.end_line}")
        lines.append("")

    return "\n".join(lines)


def format_context_headings(all_headings: List[HeadingInfo], batch_start_idx: int, batch_end_idx: int) -> str:
    """
    List headings before and after the current batch for document context.
    """
    context_lines = []
    
    # Headings before
    if batch_start_idx > 0:
        context_lines.append("## Previous context (headings only):")
        for h in all_headings[:batch_start_idx]:
            context_lines.append(f"- {h.heading_title}")
        context_lines.append("")
        
    # Headings after
    if batch_end_idx < len(all_headings) - 1:
        context_lines.append("## Subsequent context (headings only):")
        for h in all_headings[batch_end_idx + 1:]:
            context_lines.append(f"- {h.heading_title}")
        context_lines.append("")
        
    return "\n".join(context_lines)


def batch_headings(
    headings_with_chunks: List[HeadingWithChunks], 
    max_tokens_per_call: int, 
    tokens_per_word: float
) -> List[List[HeadingWithChunks]]:
    """
    Greedily pack headings into batches within token limits.
    """
    batches = []
    current_batch = []
    current_tokens = 0

    for hc in headings_with_chunks:
        # Calculate tokens for this heading and its chunks if not already done
        if hc.total_tokens == 0:
            hc.total_tokens = calculate_heading_with_chunks_tokens(hc, tokens_per_word)
        
        # If a single heading is larger than the limit, it gets its own batch
        if hc.total_tokens > max_tokens_per_call and not current_batch:
            batches.append([hc])
            continue

        if current_tokens + hc.total_tokens > max_tokens_per_call and current_batch:
            batches.append(current_batch)
            current_batch = [hc]
            current_tokens = hc.total_tokens
        else:
            current_batch.append(hc)
            current_tokens += hc.total_tokens

    if current_batch:
        batches.append(current_batch)

    return batches


def assemble_prompts(
    headings_with_chunks: List[HeadingWithChunks], 
    all_headings: List[HeadingInfo],
    session: Session, 
    settings: SummarizeSettings
) -> List[PromptBatch]:
    """
    Assemble LLM prompts by substituting content into the template.
    """
    template_str = get_active_template("summarize_sections", session)
    batches_of_headings = batch_headings(
        headings_with_chunks, 
        settings.max_tokens_per_call, 
        settings.tokens_per_word
    )
    
    prompt_batches = []
    
    # Map from heading chunk_id to its index in all_headings for context formatting
    heading_to_idx = {h.chunk_id: i for i, h in enumerate(all_headings)}
    
    for i, batch in enumerate(batches_of_headings):
        sections_content = []
        heading_ids = []
        
        # Find indices for context
        batch_start_idx = heading_to_idx[batch[0].heading.chunk_id]
        batch_end_idx = heading_to_idx[batch[-1].heading.chunk_id]
        
        for hc in batch:
            sections_content.append(format_section(hc.heading, hc.ranked_chunks))
            heading_ids.append(hc.heading.chunk_id)
            
        context_headings = format_context_headings(all_headings, batch_start_idx, batch_end_idx)
        
        # Simple substitution as per T08
        prompt_content = template_str.replace("{sections_content}", "\n\n".join(sections_content))
        prompt_content = prompt_content.replace("{context_headings}", context_headings)
        
        estimated_tokens = estimate_tokens(prompt_content, settings.tokens_per_word)
        
        prompt_batches.append(PromptBatch(
            prompt_index=i,
            content=prompt_content,
            heading_ids=heading_ids,
            estimated_tokens=estimated_tokens
        ))
        
    return prompt_batches


def generate_prompts(
    work_id: int, 
    session: Session, 
    settings: SummarizeSettings
) -> List[PromptBatch]:
    """
    Main entry point to select, rank, prune and assemble prompts.
    """
    # 1. Select headings
    all_headings = select_headings_for_summarization(work_id, session, settings)
    if not all_headings:
        return []
        
    # 2. Rank chunks for each heading
    headings_with_chunks = []
    for heading in all_headings:
        ranked_chunks = rank_content_chunks(heading, session, settings)
        hc = HeadingWithChunks(heading=heading, ranked_chunks=ranked_chunks)
        hc.total_tokens = calculate_heading_with_chunks_tokens(hc, settings.tokens_per_word)
        headings_with_chunks.append(hc)
        
    # 3. Prune to budget
    _, max_budget = calculate_total_budget(headings_with_chunks, settings)
    pruned_headings_with_chunks = prune_to_budget(headings_with_chunks, max_budget, settings)
    
    # 4. Assemble prompts
    return assemble_prompts(pruned_headings_with_chunks, all_headings, session, settings)
