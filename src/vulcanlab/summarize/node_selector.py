"""
Node Selection Module for determining which document sections to summarize.
"""

from dataclasses import dataclass
from typing import List, Dict, Tuple, Optional, Set
from sqlalchemy.orm import Session
from sqlalchemy import select, and_, or_

from vulcanlab.data.models.chunk import Chunk
from vulcanlab.data.models.summarize_settings import SummarizeSettings
from vulcanlab.data.models.sanitized_markdown import SanitizedMarkdown
from vulcanlab.summarize.salience import (
    load_salience_weights,
    compute_salience_score,
    passes_threshold,
    SalienceWeights
)

import logging

logger = logging.getLogger(__name__)

# Maximum chunk size in characters before skipping in favor of children
MAX_CHUNK_SIZE = 2_000_000


@dataclass
class SelectedNode:
    """
    Represents a document section selected for summarization.
    """
    chunk_id: int
    level: str
    content: str
    heading_path: str
    start_line: int
    end_line: int
    salience_score: float
    has_content_gap: bool


def load_heading_chunks(work_id: int, session: Session) -> List[Chunk]:
    """
    Loads heading-level chunks (H1-H5) for a given work, ordered by start_line.
    Excludes content-level chunks (e.g., H1-chunk).
    """
    stmt = (
        select(Chunk)
        .where(
            and_(
                Chunk.work_id == work_id,
                Chunk.level.in_(["H1", "H2", "H3", "H4", "H5"])
            )
        )
        .order_by(Chunk.start_line)
    )
    result = session.execute(stmt)
    return list(result.scalars().all())


def build_chunk_tree(chunks: List[Chunk]) -> Dict[int, List[Chunk]]:
    """
    Builds a parent-child hierarchy map using parent_id.
    Returns a dictionary mapping parent_id to a list of child Chunks.
    """
    tree: Dict[int, List[Chunk]] = {}
    for chunk in chunks:
        if chunk.parent_id is not None:
            if chunk.parent_id not in tree:
                tree[chunk.parent_id] = []
            tree[chunk.parent_id].append(chunk)
    
    # Sort children by start_line for each parent
    for parent_id in tree:
        tree[parent_id].sort(key=lambda c: c.start_line)
        
    return tree


def detect_content_gaps(chunks: List[Chunk], tree: Dict[int, List[Chunk]]) -> Dict[int, Tuple[int, int]]:
    """
    Identifies content gaps: regions between a heading and its first child heading.
    Returns a mapping of chunk_id -> (gap_start_line, gap_end_line).
    """
    gaps: Dict[int, Tuple[int, int]] = {}
    for chunk in chunks:
        children = tree.get(chunk.id, [])
        if children:
            first_child = children[0]
            # Gap exists if there's at least one line between heading and first child
            if first_child.start_line > chunk.start_line + 1:
                gaps[chunk.id] = (chunk.start_line + 1, first_child.start_line - 1)
    return gaps


def compute_effective_boundaries(chunk: Chunk, children: List[Chunk]) -> Tuple[int, int]:
    """
    Determines the start and end line for a chunk's own content.
    If the chunk has children, it only covers content until the first child starts.
    """
    start = chunk.start_line
    if children:
        # Effective end is just before the first child starts
        end = children[0].start_line - 1
    else:
        end = chunk.end_line
        
    return start, end


def get_content_for_node(
    lines: List[str],
    start_line: int,
    end_line: int
) -> str:
    """
    Reconstructs content from lines using line numbers.
    """
    if not lines:
        return ""
        
    # Line numbers are 1-indexed
    # Ensure indices are within bounds
    start_idx = max(0, start_line - 1)
    end_idx = min(len(lines), end_line)
    
    if start_idx >= len(lines) or start_idx >= end_idx:
        # Check if it's a single line (heading)
        if start_idx == end_idx - 1 and start_idx < len(lines):
             return lines[start_idx]
        return ""
        
    return "\n".join(lines[start_idx:end_idx])


def select_nodes_for_summarization(work_id: int, session: Session) -> List[SelectedNode]:
    """
    Main logic for selecting nodes to be summarized.
    Applies salience thresholds and handles content gaps.
    """
    # 1. Load heading chunks and build tree
    chunks = load_heading_chunks(work_id, session)
    if not chunks:
        return []
        
    tree = build_chunk_tree(chunks)
    gaps = detect_content_gaps(chunks, tree)
    weights = load_salience_weights(session)
    
    # Load sanitized markdown lines once
    stmt = select(SanitizedMarkdown).where(SanitizedMarkdown.work_id == work_id)
    result = session.execute(stmt)
    sanitized = result.scalar_one_or_none()
    lines = sanitized.content.splitlines() if sanitized and sanitized.content else []

    # 2. Identify oversized chunks that should be skipped (have children to fall back on)
    oversized_chunk_ids: Set[int] = set()
    for chunk in chunks:
        chunk_size = len(chunk.content) if chunk.content else 0
        has_children = chunk.id in tree and len(tree[chunk.id]) > 0
        if chunk_size > MAX_CHUNK_SIZE and has_children:
            logger.info(
                f"Skipping oversized chunk {chunk.id} ({chunk.level}: {chunk.heading_breadcrumbs}) "
                f"with {chunk_size:,} chars - relying on {len(tree[chunk.id])} child chunks"
            )
            oversized_chunk_ids.add(chunk.id)

    # 3. Compute salience scores (skip oversized chunks)
    # We need total_chunks for location prior
    total_chunks = len(chunks)
    seen_keyphrases: Set[str] = set()

    chunk_scores: Dict[int, float] = {}
    for i, chunk in enumerate(chunks):
        if chunk.id in oversized_chunk_ids:
            chunk_scores[chunk.id] = 0.0  # Placeholder score for skipped chunks
            continue
        score = compute_salience_score(
            chunk_content=chunk.content,
            heading_level=chunk.level,
            weights=weights,
            seen_keyphrases=seen_keyphrases,
            chunk_index=i,
            total_chunks=total_chunks
        )
        chunk_scores[chunk.id] = score

    # 4. Handle H2 top-percent filtering
    h2_chunks = [c for c in chunks if c.level == "H2"]
    h2_to_keep = set()
    if h2_chunks:
        # Sort H2s by score descending
        sorted_h2 = sorted(h2_chunks, key=lambda c: chunk_scores[c.id], reverse=True)
        num_to_keep = max(1, int(len(h2_chunks) * (weights.h2_top_percent / 100.0)))
        h2_to_keep = {c.id for c in sorted_h2[:num_to_keep]}

    # 5. Filter and build SelectedNode list
    selected_nodes: List[SelectedNode] = []
    
    for chunk in chunks:
        # Skip oversized chunks (already logged above)
        if chunk.id in oversized_chunk_ids:
            continue

        score = chunk_scores[chunk.id]
        is_selected = False

        if chunk.level == "H1":
            is_selected = weights.h1_always_summarize
        elif chunk.level == "H2":
            is_selected = chunk.id in h2_to_keep
        else:
            # H3, H4, H5 use thresholds
            is_selected = passes_threshold(score, chunk.level, weights)
            
        if is_selected:
            # Add the main heading node (just the heading)
            heading_content = get_content_for_node(lines, chunk.start_line, chunk.start_line)
            
            selected_nodes.append(SelectedNode(
                chunk_id=chunk.id,
                level=chunk.level,
                content=heading_content,
                heading_path=chunk.heading_breadcrumbs or "",
                start_line=chunk.start_line,
                end_line=chunk.start_line,
                salience_score=score,
                has_content_gap=chunk.id in gaps
            ))
            
            # If there's a content gap, add it as an additional node
            if chunk.id in gaps:
                gap_start, gap_end = gaps[chunk.id]
                gap_content = get_content_for_node(lines, gap_start, gap_end)
                
                selected_nodes.append(SelectedNode(
                    chunk_id=chunk.id,
                    level=f"{chunk.level}-content", # Use -content suffix for gaps
                    content=gap_content,
                    heading_path=chunk.heading_breadcrumbs or "",
                    start_line=gap_start,
                    end_line=gap_end,
                    salience_score=score,
                    has_content_gap=False # This is the gap itself
                ))
            elif not tree.get(chunk.id):
                # If no children and no gap was detected (because gaps are only before children),
                # the "gap" is actually just the content of the chunk.
                # In our case, if there are no children, the chunk's content extends to end_line.
                if chunk.end_line > chunk.start_line:
                    content_start = chunk.start_line + 1
                    content_end = chunk.end_line
                    content = get_content_for_node(lines, content_start, content_end)
                    
                    if content.strip():
                        selected_nodes.append(SelectedNode(
                            chunk_id=chunk.id,
                            level=f"{chunk.level}-content",
                            content=content,
                            heading_path=chunk.heading_breadcrumbs or "",
                            start_line=content_start,
                            end_line=content_end,
                            salience_score=score,
                            has_content_gap=False
                        ))
    
    return selected_nodes
