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
from vulcanlab.utils.file_utils import compute_file_hash, get_path_resolver
from vulcanlab.utils.rag_config_loader import get_default_config, get_config_by_name
from vulcanlab.config.app_config import load_config


# Initialize path resolver
resolver = get_path_resolver()




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
DEFAULT_MIN_CONTENT_LENGTH = 350  # Minimum characters in content for final output
DEFAULT_ENRICH_FROM_MD = True # Read content from markdown file during consolidation


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


def _read_content_from_file(
    markdown_path: Path,
    start_line: int,
    end_line: int
) -> str:
    """Read content from markdown file by line range."""
    lines = markdown_path.read_text(encoding='utf-8').splitlines()
    # Convert to 0-indexed
    return '\n'.join(lines[start_line - 1:end_line])


def _calculate_coverage(
    items: list[dict],
    parent_start: int,
    parent_end: int
) -> float:
    """Calculate what percentage of parent is covered by items."""
    parent_lines = parent_end - parent_start + 1
    if parent_lines <= 0:
        return 0.0

    # Count covered lines
    covered = set()
    for item in items:
        for line in range(item['start_line'], item['end_line'] + 1):
            covered.add(line)

    # Only count lines within parent range
    covered_in_parent = covered & set(range(parent_start, parent_end + 1))
    return len(covered_in_parent) / parent_lines


def _merge_adjacent_items(
    items: list[dict],
    markdown_path: Path,
    line_gap: int = DEFAULT_LINE_GAP,
    enrich_from_md: bool = DEFAULT_ENRICH_FROM_MD
) -> list[dict]:
    """Merge items that are within line_gap of each other."""
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
            merged.append(_finalize_group(current_group, markdown_path, enrich_from_md))
            current_group = [item]

    # Finalize last group
    if current_group:
        merged.append(_finalize_group(current_group, markdown_path, enrich_from_md))

    return merged


def _finalize_group(
    items: list[dict],
    markdown_path: Path,
    enrich_from_md: bool = DEFAULT_ENRICH_FROM_MD
) -> dict:
    """Create a merged item from a group of items."""
    chunk_ids = []
    for item in items:
        if 'chunk_ids' in item:
            chunk_ids.extend(item['chunk_ids'])
        else:
            chunk_ids.append(item['id'])

    start_line = min(item['start_line'] for item in items)
    end_line = max(item['end_line'] for item in items)
    score = max(item.get('score', item.get('final_score', 0)) for item in items)

    # Get content: either from file or from existing items
    if enrich_from_md:
        # Read content from markdown file
        content = _read_content_from_file(markdown_path, start_line, end_line)
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
    enrich_from_md: bool | None = None,
    config_preset: str | None = None,
    verbose: bool = False
) -> ConsolidationResult:
    """Consolidate retrieved context by grouping and merging chunks.

    Args:
        query_id: ID of the Query in the database
        coverage_threshold: Threshold for replacing with parent. If None, uses config.
        line_gap: Max lines between chunks to merge. If None, uses config.
        min_content_length: Minimum characters in content for final output. If None, uses config.
        enrich_from_md: Read content from markdown file during consolidation. If None, uses config.
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

    # Use provided parameters or fall back to config
    coverage_threshold = coverage_threshold if coverage_threshold is not None else consolidation_params["coverage_threshold"]
    line_gap = line_gap if line_gap is not None else consolidation_params["line_gap"]
    min_content_length = min_content_length if min_content_length is not None else consolidation_params["min_content_length"]
    enrich_from_md = enrich_from_md if enrich_from_md is not None else consolidation_params["enrich_from_md"]

    if verbose:
        print(f"Using RAG config preset: {config_preset or 'default'}")
        print(f"  coverage_threshold={coverage_threshold}, line_gap={line_gap}, enrich_from_md={enrich_from_md}")

    # Initialize logging
    log_data = {
        "query_id": query_id,
        "timestamp": datetime.now().isoformat(),
        "config": {
            "preset": config_preset or "default",
            "coverage_threshold": coverage_threshold,
            "line_gap": line_gap,
            "min_content_length": min_content_length,
            "enrich_from_md": enrich_from_md,
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

        # Verify content hashes
        for work_id, work in works_map.items():
            if work.files and "sanitized" in work.files:
                md_path = resolver.resolve_work_path(work, "sanitized")
                stored_hash = work.files["sanitized"].get("hash")

                if md_path.exists() and stored_hash:
                    current_hash = compute_file_hash(md_path)
                    if current_hash != stored_hash:
                        raise RuntimeError(
                            f"Content hash mismatch for work {work_id} ({work.title}). "
                            f"Sanitized file may have been modified. Cannot consolidate."
                        )

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
                if not work or not work.files or "sanitized" not in work.files:
                    new_items.extend(group_items)
                    continue

                md_path = resolver.resolve_work_path(work, "sanitized")
                if not md_path.exists():
                    new_items.extend(group_items)
                    continue

                # Check if parent exists
                if parent_id and parent_id in parents_map:
                    parent = parents_map[parent_id]

                    # Calculate coverage
                    coverage = _calculate_coverage(
                        group_items,
                        parent.start_line,
                        parent.end_line
                    )

                    if coverage >= coverage_threshold and enrich_from_md:
                        # Replace with parent content (only if enrich_from_md is True)
                        content = _read_content_from_file(
                            md_path,
                            parent.start_line,
                            parent.end_line
                        )
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
                        # Merge adjacent items
                        merged = _merge_adjacent_items(group_items, md_path, line_gap, enrich_from_md)
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
                    merged = _merge_adjacent_items(group_items, md_path, line_gap, enrich_from_md)
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
