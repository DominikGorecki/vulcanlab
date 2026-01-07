"""
Hybrid search combining lexical and dense results using Reciprocal Rank Fusion (RRF).
"""

import logging
from typing import List, Tuple, Dict, Any
from sqlalchemy.orm import Session

from .search_lexical import search_lexical
from .search_dense import search_dense

logger = logging.getLogger(__name__)


def search_hybrid(
    query: str,
    session: Session,
    page: int = 1,
    page_size: int = 20,
    headings_only: bool = False,
    rrf_k: int = 60,
    dense_top_k: int = 20,
    lexical_top_k: int = 20,
    dense_weight: float = 0.5,
    lexical_weight: float = 0.5
) -> Tuple[List[Dict[str, Any]], Dict[str, Any], int]:
    """
    Perform hybrid search using Reciprocal Rank Fusion (RRF).

    Combines results from lexical (keyword) search and dense (semantic) search.
    RRF score formula: score = sum(weight_i * (1 / (k + rank_i)))

    Args:
        query: Search query string
        session: SQLAlchemy session
        page: Page number (1-indexed)
        page_size: Results per page
        headings_only: Whether to search only heading chunks
        rrf_k: Smoothing constant for RRF (default 60)
        dense_top_k: Number of candidates to fetch from dense search
        lexical_top_k: Number of candidates to fetch from lexical search
        dense_weight: Weight for dense search results
        lexical_weight: Weight for lexical search results

    Returns:
        Tuple of (results list, rrf_stats dict, total count)
    """
    if page < 1:
        raise ValueError("Page must be >= 1")
    if page_size < 1:
        raise ValueError("Page size must be >= 1")
    if rrf_k < 1:
        raise ValueError("RRF k must be >= 1")

    # Normalize weights
    total_weight = dense_weight + lexical_weight
    if total_weight <= 0:
        dense_weight, lexical_weight = 0.5, 0.5
    else:
        dense_weight /= total_weight
        lexical_weight /= total_weight

    # 1. Fetch candidates from both sources
    # We fetch more candidates than page_size to ensure good fusion quality
    dense_results, _ = search_dense(
        query=query,
        session=session,
        page=1,
        page_size=dense_top_k,
        headings_only=headings_only,
        top_k=dense_top_k
    )

    lexical_results, _ = search_lexical(
        query=query,
        session=session,
        page=1,
        page_size=lexical_top_k,
        headings_only=headings_only,
        top_k=lexical_top_k
    )

    # 2. Map chunk IDs to results and calculate ranks
    fused_results = {}  # chunk_id -> result_dict
    
    # Track ranks
    dense_ranks = {res["id"]: i + 1 for i, res in enumerate(dense_results)}
    lexical_ranks = {res["id"]: i + 1 for i, res in enumerate(lexical_results)}
    
    # Combine unique chunk IDs
    all_chunk_ids = set(dense_ranks.keys()) | set(lexical_ranks.keys())
    
    # Store result data from either source (they should be identical for same ID)
    chunk_data = {}
    for res in dense_results:
        chunk_data[res["id"]] = res
    for res in lexical_results:
        # Lexical results might have data not in dense results if no overlap
        if res["id"] not in chunk_data:
            chunk_data[res["id"]] = res

    # 3. Apply RRF formula
    penalty_rank = 999999
    
    for chunk_id in all_chunk_ids:
        d_rank = dense_ranks.get(chunk_id, penalty_rank)
        l_rank = lexical_ranks.get(chunk_id, penalty_rank)
        
        # Calculate RRF score
        # score = dense_weight * (1 / (rrf_k + d_rank)) + lexical_weight * (1 / (rrf_k + l_rank))
        score = (dense_weight / (rrf_k + d_rank)) + (lexical_weight / (rrf_k + l_rank))
        
        # Prepare result dict
        res = chunk_data[chunk_id].copy()
        # Remove component scores to avoid confusion
        res.pop("similarity_score", None)
        res.pop("rank_score", None)
        
        res.update({
            "rrf_score": score,
            "dense_rank": dense_ranks.get(chunk_id),
            "lexical_rank": lexical_ranks.get(chunk_id)
        })
        
        fused_results[chunk_id] = res

    # 4. Sort and Paginate
    sorted_results = sorted(
        fused_results.values(),
        key=lambda x: x["rrf_score"],
        reverse=True
    )
    
    total_count = len(sorted_results)
    start_idx = (page - 1) * page_size
    end_idx = start_idx + page_size
    paginated_results = sorted_results[start_idx:end_idx]

    # 5. Metadata
    rrf_stats = {
        "dense_candidates": len(dense_results),
        "lexical_candidates": len(lexical_results),
        "fused_count": total_count,
        "rrf_k": rrf_k
    }

    logger.info(
        f"Hybrid search: query='{query}', fused {total_count} results from "
        f"{len(dense_results)} dense + {len(lexical_results)} lexical candidates"
    )

    return paginated_results, rrf_stats, total_count

