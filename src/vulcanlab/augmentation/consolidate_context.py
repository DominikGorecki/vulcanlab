"""
Context consolidation for clean retrieval results.

This module consolidates retrieved chunks by grouping them under parents
and merging adjacent chunks to create cleaner context for augmentation.

Usage:
    from vulcanlab.augmentation.consolidate_context import consolidate_context
    result = consolidate_context(query_id=1, verbose=True)
"""

from collections import defaultdict
from dataclasses import dataclass, field
from datetime import datetime
from pathlib import Path
import json

from vulcanlab.data.database import get_session
from vulcanlab.data.models import Chunk, Query, Work
from vulcanlab.utils.rag_config_loader import get_default_config, get_config_by_name, get_config_value
from vulcanlab.config.app_config import load_config

import logging

logger = logging.getLogger(__name__)






@dataclass
class ConsolidatedGroup:
    """A consolidated group of chunks."""

    chunk_ids: list[int]
    parent_id: int | None
    work_id: int
    content: str
    start_line: int
    end_line: int
    score: float
    heading_chain: list[str] | None = None  # Breadcrumb trail of section headings


@dataclass
class ConsolidationResult:
    """Result of the consolidation operation."""

    query_id: int
    original_count: int
    consolidated_count: int
    groups: list[ConsolidatedGroup]


# Default parameters
DEFAULT_COVERAGE_THRESHOLD = 0.5
DEFAULT_LINE_GAP = 7
DEFAULT_MIN_CONTENT_LENGTH = 350
DEFAULT_ENRICH_FROM_PARENT = True


def _serialize_group_for_log(group: ConsolidatedGroup) -> dict:
    """Serialize a ConsolidatedGroup to a JSON-serializable dict."""
    return {
        "chunk_ids": group.chunk_ids,
        "parent_id": group.parent_id,
        "work_id": group.work_id,
        "content": group.content,
        "start_line": group.start_line,
        "end_line": group.end_line,
        "score": group.score,
        "heading_chain": group.heading_chain,
    }


def _serialize_item_for_log(item: dict) -> dict:
    """Serialize an item dict for logging."""
    return {
        "id": item.get('id'),
        "chunk_ids": item.get('chunk_ids', []),
        "parent_id": item.get('parent_id'),
        "work_id": item.get('work_id'),
        "content": item.get('content', '')[:500],  # Truncate for logging
        "start_line": item.get('start_line'),
        "end_line": item.get('end_line'),
        "score": item.get('score', 0),
        "level": item.get('level', 'chunk'),
    }


def _save_consolidation_log(query_id: int, log_data: dict) -> None:
    """Save consolidation log to JSON file."""
    config = load_config()
    if not config.logging.enabled:
        return
    
    logs_dir = Path(config.logging.log_dir)
    logs_dir.mkdir(exist_ok=True)
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    log_file = logs_dir / f"consolidate_query_{query_id}_{timestamp}.json"
    
    with open(log_file, 'w', encoding='utf-8') as f:
        json.dump(log_data, f, indent=2, ensure_ascii=False)


def _get_level_order(level: str) -> int:
    """Get numeric order for heading level (higher = deeper)."""
    level_map = {
        "H1": 1, "H2": 2, "H3": 3, "H4": 4, "H5": 5,
        "sentence": 6, "chunk": 7
    }
    return level_map.get(level, 10)


def _get_heading_chain(
    parent_id: int | None,
    parents_map: dict
) -> list[str]:
    """Get heading breadcrumbs from parent chunk's heading_breadcrumbs field.

    Returns a list of heading texts from root (H1) to the immediate parent,
    providing hierarchical context for the chunk.

    Args:
        parent_id: The parent_id of the current chunk/group
        parents_map: Dict mapping chunk_id to Chunk objects

    Returns:
        List of heading texts, e.g., ["Chapter 5: Therapy", "Schema Therapy", "Core Techniques"]
    """
    if not parent_id or parent_id not in parents_map:
        return []

    parent = parents_map[parent_id]

    # Use heading_breadcrumbs field if available
    if parent.heading_breadcrumbs:
        # Split by " > " separator and return as list
        return [h.strip() for h in parent.heading_breadcrumbs.split(' > ') if h.strip()]

    # Fallback: return empty list if no breadcrumbs
    return []




def _extract_content_from_parent(
    parent: Chunk,
    start_line: int,
    end_line: int
) -> str:
    """Extract content from parent chunk by line range.

    Args:
        parent: Parent Chunk object with content
        start_line: Starting line number (1-indexed, inclusive)
        end_line: Ending line number (1-indexed, inclusive)

    Returns:
        Extracted content as string
    """
    if not parent or not parent.content:
        return ""

    parent_lines = parent.content.split('\n')

    # Clamp bounds to parent content
    start_idx = max(0, start_line - 1)  # Convert to 0-indexed
    end_idx = min(len(parent_lines), end_line)  # end_line is inclusive, but slicing is exclusive

    return '\n'.join(parent_lines[start_idx:end_idx])


def _calculate_coverage(
    items: list[dict],
    parent: Chunk
) -> float:
    """Calculate what percentage of parent content is covered by child items.

    Uses character count instead of line count for more accurate coverage.

    Args:
        items: List of child item dictionaries with 'content' field
        parent: Parent Chunk object with content field

    Returns:
        Coverage ratio (0.0 to 1.0) based on character counts
    """
    if not parent or not parent.content:
        return 0.0

    parent_char_count = len(parent.content)
    if parent_char_count == 0:
        return 0.0

    # Sum character counts from all child items
    child_char_count = sum(len(item.get('content', '')) for item in items)

    return child_char_count / parent_char_count


def _merge_adjacent_items(
    items: list[dict],
    parent: Chunk | None,
    line_gap: int = DEFAULT_LINE_GAP,
    enrich_from_parent: bool = DEFAULT_ENRICH_FROM_PARENT
) -> list[dict]:
    """Merge items that are within line_gap of each other.

    Args:
        items: List of item dictionaries to merge
        parent: Parent Chunk object (used for content extraction)
        line_gap: Maximum line gap between items to merge them
        enrich_from_parent: Whether to extract content from parent chunk

    Returns:
        List of merged item dictionaries
    """
    if not items:
        return []

    # Sort by start_line
    sorted_items = sorted(items, key=lambda x: x['start_line'])

    merged = []
    current_group = [sorted_items[0]]

    for item in sorted_items[1:]:
        last = current_group[-1]
        # Check if within gap
        if item['start_line'] - last['end_line'] <= line_gap:
            current_group.append(item)
        else:
            # Finalize current group
            merged.append(_finalize_group(current_group, parent, enrich_from_parent))
            current_group = [item]

    # Finalize last group
    if current_group:
        merged.append(_finalize_group(current_group, parent, enrich_from_parent))

    return merged


def _finalize_group(
    items: list[dict],
    parent: Chunk | None,
    enrich_from_parent: bool = DEFAULT_ENRICH_FROM_PARENT
) -> dict:
    """Create a merged item from a group of items.

    Args:
        items: List of items to merge
        parent: Parent Chunk object
        enrich_from_parent: Whether to extract content from parent vs concatenating existing content

    Returns:
        Dictionary representing the merged item
    """
    chunk_ids = []
    for item in items:
        if 'chunk_ids' in item:
            chunk_ids.extend(item['chunk_ids'])
        else:
            chunk_ids.append(item['id'])

    start_line = min(item['start_line'] for item in items)
    end_line = max(item['end_line'] for item in items)
    score = max(item.get('score', item.get('final_score', 0)) for item in items)

    # Get content: priority order is parent chunk > existing content
    content = ""
    if enrich_from_parent:
        if parent and parent.content:
            # Use parent chunk content (no file I/O)
            content = _extract_content_from_parent(parent, start_line, end_line)
        else:
            # Fallback to concatenating existing content
            content = '\n\n'.join(item['content'] for item in items if item.get('content'))
    else:
        # Use existing content from items (concatenate with newlines)
        content = '\n\n'.join(item['content'] for item in items if item.get('content'))

    # Get heading from first item's heading_breadcrumbs
    first_item = items[0]
    heading_to_prepend = None

    if 'heading_breadcrumbs' in first_item and first_item['heading_breadcrumbs']:
        breadcrumbs = first_item['heading_breadcrumbs']

        # Handle both string and list formats
        if isinstance(breadcrumbs, str):
            breadcrumb_list = [h.strip() for h in breadcrumbs.split(' > ') if h.strip()]
        elif isinstance(breadcrumbs, list):
            breadcrumb_list = breadcrumbs
        else:
            breadcrumb_list = []

        # Get the last (most specific) heading
        if breadcrumb_list:
            last_heading = breadcrumb_list[-1]

            # Get level and construct markdown heading
            level = first_item.get('level', 'chunk')
            if level in ['H1', 'H2', 'H3', 'H4', 'H5']:
                level_num = int(level[1])  # Extract number from 'H1', 'H2', etc.
                heading_to_prepend = '#' * level_num + ' ' + last_heading
            else:
                heading_to_prepend = last_heading

    # Only prepend if content doesn't already start with this heading
    if heading_to_prepend and not content.startswith(heading_to_prepend):
        content = heading_to_prepend + '\n\n' + content

    return {
        'chunk_ids': chunk_ids,
        'parent_id': items[0].get('parent_id'),
        'work_id': items[0]['work_id'],
        'content': content,
        'start_line': start_line,
        'end_line': end_line,
        'score': score
    }


def consolidate_context(
    query_id: int,
    coverage_threshold: float | None = None,
    line_gap: int | None = None,
    min_content_length: int | None = None,
    enrich_from_parent: bool | None = None,
    config_preset: str | None = None,
    verbose: bool = False
) -> ConsolidationResult:
    """Consolidate retrieved context by grouping and merging chunks.

    Args:
        query_id: ID of the Query in the database
        coverage_threshold: Threshold for replacing with parent. If None, uses config.
        line_gap: Max lines between chunks to merge. If None, uses config.
        min_content_length: Minimum characters in content for final output. If None, uses config.
        enrich_from_parent: Enrich from parent chunk during consolidation. If None, uses config.
        config_preset: Name of RAG config preset to use. If None, uses default.
        verbose: Print progress information

    Returns:
        ConsolidationResult with consolidated groups

    Raises:
        ValueError: If query not found or no retrieved context, or if config preset not found
        RuntimeError: If markdown file hash doesn't match
    """
    # Load configuration
    if config_preset:
        config = get_config_by_name(config_preset)
    else:
        config = get_default_config()

    consolidation_params = config["consolidation"]

    # Use provided parameters or fall back to config (with backwards compatibility)
    coverage_threshold = coverage_threshold if coverage_threshold is not None else get_config_value(config, "consolidation", "coverage_threshold", DEFAULT_COVERAGE_THRESHOLD)
    line_gap = line_gap if line_gap is not None else get_config_value(config, "consolidation", "line_gap", DEFAULT_LINE_GAP)
    min_content_length = min_content_length if min_content_length is not None else get_config_value(config, "consolidation", "min_content_length", DEFAULT_MIN_CONTENT_LENGTH)
    enrich_from_parent = enrich_from_parent if enrich_from_parent is not None else get_config_value(config, "consolidation", "enrich_from_parent", DEFAULT_ENRICH_FROM_PARENT)

    if verbose:
        print(f"Using RAG config preset: {config_preset or 'default'}")
        print(f"  coverage_threshold={coverage_threshold}, line_gap={line_gap}, enrich_from_parent={enrich_from_parent}")

    # Initialize logging
    log_data = {
        "query_id": query_id,
        "timestamp": datetime.now().isoformat(),
        "config": {
            "preset": config_preset or "default",
            "coverage_threshold": coverage_threshold,
            "line_gap": line_gap,
            "min_content_length": min_content_length,
            "enrich_from_parent": enrich_from_parent,
        },
        "iterations": []
    }

    with get_session() as session:
        # Fetch query
        query = session.query(Query).filter(Query.id == query_id).first()
        if not query:
            raise ValueError(f"Query with ID {query_id} not found")

        if not query.retrieved_context:
            raise ValueError(f"Query {query_id} has no retrieved_context")

        if verbose:
            print(f"Consolidating context for query {query_id}")
            print(f"  Original items: {len(query.retrieved_context)}")

        # Get all work IDs and fetch works
        work_ids = {item['work_id'] for item in query.retrieved_context}
        works = session.query(Work).filter(Work.id.in_(work_ids)).all()
        works_map = {w.id: w for w in works}


        # Get all parent chunks we need
        parent_ids = {item['parent_id'] for item in query.retrieved_context if item.get('parent_id')}
        parents = session.query(Chunk).filter(Chunk.id.in_(parent_ids)).all()
        parents_map = {p.id: p for p in parents}

        # Build hierarchy: get parents of parents for nested consolidation
        all_parent_ids = set(parent_ids)
        parents_to_check = list(parent_ids)
        while parents_to_check:
            next_level = session.query(Chunk).filter(Chunk.id.in_(parents_to_check)).all()
            parents_to_check = []
            for p in next_level:
                if p.parent_id and p.parent_id not in all_parent_ids:
                    all_parent_ids.add(p.parent_id)
                    parents_to_check.append(p.parent_id)

        # Fetch all parents
        all_parents = session.query(Chunk).filter(Chunk.id.in_(all_parent_ids)).all()
        parents_map = {p.id: p for p in all_parents}

        # Convert retrieved_context to working items
        items = []
        for ctx in query.retrieved_context:
            items.append({
                'id': ctx['id'],
                'chunk_ids': [ctx['id']],
                'parent_id': ctx.get('parent_id'),
                'work_id': ctx['work_id'],
                'content': ctx.get('content', ''),
                'start_line': ctx['start_line'],
                'end_line': ctx['end_line'],
                'score': ctx.get('final_score', 0),
                'level': ctx.get('level', 'chunk')
            })
        
        if load_config().logging.enabled:
            log_data["original_items"] = [_serialize_item_for_log(item) for item in items]

        # Get unique levels and sort by depth (deepest first)
        parent_levels = {}
        for item in items:
            if item['parent_id'] and item['parent_id'] in parents_map:
                parent = parents_map[item['parent_id']]
                parent_levels[item['parent_id']] = parent.level

        # Process from deepest level to shallowest
        processed = True
        iteration = 0
        while processed:
            processed = False
            iteration += 1
            
            if load_config().logging.enabled:
                iteration_log = {
                    "iteration": iteration,
                    "items_before": len(items),
                    "items": [_serialize_item_for_log(item) for item in items],
                    "operations": []
                }

            # Group by (work_id, parent_id)
            groups = defaultdict(list)
            for item in items:
                key = (item['work_id'], item.get('parent_id'))
                groups[key].append(item)

            new_items = []

            for (work_id, parent_id), group_items in groups.items():
                work = works_map.get(work_id)

                # Get parent chunk if available
                parent = None
                if parent_id and parent_id in parents_map:
                    parent = parents_map[parent_id]

                    # Calculate coverage using character counts
                    coverage = _calculate_coverage(group_items, parent)

                    if coverage >= coverage_threshold:
                        # Replace with parent content (no file I/O)
                        if parent.content:
                            content = parent.content
                        else:
                            # Fallback: concatenate child content if parent has no content
                            content = '\n\n'.join(item['content'] for item in group_items if item.get('content'))

                        score = max(item['score'] for item in group_items)
                        chunk_ids = []
                        for item in group_items:
                            chunk_ids.extend(item.get('chunk_ids', [item.get('id')]))

                        new_item = {
                            'chunk_ids': chunk_ids,
                            'parent_id': parent.parent_id,  # Move up one level
                            'work_id': work_id,
                            'content': content,
                            'start_line': parent.start_line,
                            'end_line': parent.end_line,
                            'score': score,
                            'level': parent.level
                        }
                        new_items.append(new_item)
                        processed = True

                        if verbose:
                            print(f"  Replaced {len(group_items)} items with parent {parent_id} ({coverage:.0%} coverage)")

                        if load_config().logging.enabled:
                            iteration_log["operations"].append({
                                "type": "replace_with_parent",
                                "parent_id": parent_id,
                                "coverage": coverage,
                                "items_replaced": len(group_items),
                                "item_ids": [item.get('id') for item in group_items],
                                "new_item": _serialize_item_for_log(new_item)
                            })
                    else:
                        # Merge adjacent items using parent chunk
                        merged = _merge_adjacent_items(group_items, parent, line_gap, enrich_from_parent)
                        if len(merged) < len(group_items):
                            processed = True
                            if verbose:
                                print(f"  Merged {len(group_items)} items into {len(merged)} (parent {parent_id})")

                            if load_config().logging.enabled:
                                iteration_log["operations"].append({
                                    "type": "merge_adjacent",
                                    "parent_id": parent_id,
                                    "items_before": len(group_items),
                                    "items_after": len(merged),
                                    "merged_items": [_serialize_item_for_log(item) for item in merged]
                                })
                        new_items.extend(merged)
                else:
                    # No parent, just merge adjacent
                    merged = _merge_adjacent_items(group_items, None, line_gap, enrich_from_parent)
                    if len(merged) < len(group_items):
                        processed = True

                        if load_config().logging.enabled:
                            iteration_log["operations"].append({
                                "type": "merge_adjacent_no_parent",
                                "work_id": work_id,
                                "items_before": len(group_items),
                                "items_after": len(merged),
                                "merged_items": [_serialize_item_for_log(item) for item in merged]
                            })
                    new_items.extend(merged)

            if load_config().logging.enabled:
                iteration_log["items_after"] = len(new_items)
                iteration_log["new_items"] = [_serialize_item_for_log(item) for item in new_items]
                log_data["iterations"].append(iteration_log)

            items = new_items

        # Build final result with heading breadcrumbs
        groups = []
        for item in items:
            # Compute heading chain from parent hierarchy
            heading_chain = _get_heading_chain(item.get('parent_id'), parents_map)

            groups.append(ConsolidatedGroup(
                chunk_ids=item.get('chunk_ids', [item.get('id')]),
                parent_id=item.get('parent_id'),
                work_id=item['work_id'],
                content=item['content'],
                start_line=item['start_line'],
                end_line=item['end_line'],
                score=item['score'],
                heading_chain=heading_chain
            ))

        # Sort by score descending
        groups.sort(key=lambda x: x.score, reverse=True)

        # Filter out groups with content shorter than minimum length
        pre_filter_count = len(groups)
        filtered_groups = [g for g in groups if len(g.content) < min_content_length]
        groups = [g for g in groups if len(g.content) >= min_content_length]

        if verbose:
            print(f"  Consolidated count: {len(groups)}")
            if pre_filter_count > len(groups):
                filtered_count = pre_filter_count - len(groups)
                print(f"  Filtered out {filtered_count} items with content < {min_content_length} characters")
        
        if load_config().logging.enabled:
            log_data["final_groups"] = [_serialize_group_for_log(group) for group in groups]
            log_data["filtered_groups"] = [_serialize_group_for_log(group) for group in filtered_groups]
            log_data["filtering"] = {
                "before_count": pre_filter_count,
                "after_count": len(groups),
                "filtered_count": len(filtered_groups),
                "min_content_length": min_content_length
            }

        # Save to database
        context_data = []
        for group in groups:
            context_data.append({
                'chunk_ids': group.chunk_ids,
                'parent_id': group.parent_id,
                'work_id': group.work_id,
                'content': group.content,
                'start_line': group.start_line,
                'end_line': group.end_line,
                'score': group.score,
                'heading_chain': group.heading_chain  # Store as list, not joined string
            })

        query.clean_retrieval_context = context_data
        session.commit()

        if verbose:
            print(f"  Saved to query.clean_retrieval_context")

        # Save log file
        # Save log file
        if load_config().logging.enabled:
            _save_consolidation_log(query_id, log_data)

        return ConsolidationResult(
            query_id=query_id,
            original_count=len(query.retrieved_context),
            consolidated_count=len(groups),
            groups=groups
        )
