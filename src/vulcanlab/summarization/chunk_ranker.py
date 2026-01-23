"""
Chunk ranking logic using dense search, lexical search, and Reciprocal Rank Fusion (RRF).
"""

import logging
import math
import re
from dataclasses import dataclass
from typing import List, Tuple, Optional, Dict

from sqlalchemy import text, select
from sqlalchemy.orm import Session

from vulcanlab.data.models.chunk import Chunk
from vulcanlab.data.models.summarize_settings import SummarizeSettings
from vulcanlab.summarization.heading_selector import HeadingInfo

logger = logging.getLogger(__name__)

@dataclass
class RankedChunk:
    """Dataclass for ranked chunk results with all scores."""
    chunk_id: int
    content: str
    word_count: int
    start_line: int
    end_line: int
    dense_score: Optional[float] = None
    dense_rank: Optional[int] = None
    lexical_score: Optional[float] = None
    lexical_rank: Optional[int] = None
    rrf_score: float = 0.0
    mmr_score: Optional[float] = None
    rank_position: Optional[int] = None

def build_search_query(heading_breadcrumbs: Optional[str], heading_title: str) -> str:
    """
    Combine breadcrumbs and title for search query.
    Strip markdown formatting and normalize whitespace.
    """
    # Combine breadcrumbs and title
    components = []
    if heading_breadcrumbs:
        # Breadcrumbs are often like "H1 > H2 > H3"
        components.append(heading_breadcrumbs.replace(">", " "))
    
    components.append(heading_title)
    query = " ".join(components)
    
    # Strip markdown bold/italic
    query = re.sub(r'[*_]{1,3}', '', query)
    
    # Normalize whitespace
    query = " ".join(query.split())
    
    return query.strip()

def search_dense(
    query: str,
    content_chunk_ids: List[int],
    session: Session,
    top_k: int
) -> List[Tuple[int, float]]:
    """
    Search chunks table with pgvector cosine similarity.
    Filter to only content_chunk_ids (children of heading).
    """
    if not content_chunk_ids:
        return []

    # Lazy import for AI dependencies
    from vulcanlab.ai.llm_factory import create_embeddings
    
    try:
        embeddings_model = create_embeddings()
        query_embedding = embeddings_model.embed_query(query)
    except Exception as e:
        logger.error(f"Failed to generate query embedding for dense search: {e}")
        return []

    embedding_str = '[' + ','.join(str(x) for x in query_embedding) + ']'
    
    # Use text() for pgvector distance operator <=>
    stmt = text("""
        SELECT id, 1 - (embedding <=> :embedding) as score
        FROM chunks
        WHERE id = ANY(:chunk_ids)
          AND embedding IS NOT NULL
        ORDER BY score DESC
        LIMIT :top_k
    """)
    
    results = session.execute(
        stmt, 
        {"embedding": embedding_str, "chunk_ids": content_chunk_ids, "top_k": top_k}
    ).fetchall()
    
    return [(row[0], float(row[1])) for row in results]

def search_lexical(
    query: str,
    content_chunk_ids: List[int],
    session: Session,
    top_k: int
) -> List[Tuple[int, float]]:
    """
    Use PostgreSQL ts_rank with plainto_tsquery.
    Filter to only content_chunk_ids.
    """
    if not content_chunk_ids:
        return []

    # Sanitize for tsquery - using plainto_tsquery as per spec
    # It handles spaces and special characters automatically
    
    stmt = text("""
        SELECT id, ts_rank_cd(content_tsvector, plainto_tsquery('english', :query)) as score
        FROM chunks
        WHERE id = ANY(:chunk_ids)
        ORDER BY score DESC
        LIMIT :top_k
    """)
    
    results = session.execute(
        stmt, 
        {"query": query, "chunk_ids": content_chunk_ids, "top_k": top_k}
    ).fetchall()
    
    return [(row[0], float(row[1])) for row in results]

def fuse_rrf(
    dense_results: List[Tuple[int, float]],
    lexical_results: List[Tuple[int, float]],
    chunk_data_map: dict,
    k: int,
    top_k: int
) -> List[RankedChunk]:
    """
    Apply RRF formula: score = 1/(k + rank_dense) + 1/(k + rank_lexical)
    """
    dense_ranks = {cid: i + 1 for i, (cid, score) in enumerate(dense_results)}
    lexical_ranks = {cid: i + 1 for i, (cid, score) in enumerate(lexical_results)}
    
    dense_scores = {cid: score for cid, score in dense_results}
    lexical_scores = {cid: score for cid, score in lexical_results}
    
    all_ids = set(dense_ranks.keys()) | set(lexical_ranks.keys())
    
    penalty_rank = 999999
    
    ranked_chunks = []
    for cid in all_ids:
        d_rank = dense_ranks.get(cid, penalty_rank)
        l_rank = lexical_ranks.get(cid, penalty_rank)
        
        rrf_score = (1.0 / (k + d_rank)) + (1.0 / (k + l_rank))
        
        chunk = chunk_data_map[cid]
        word_count = len(chunk.content.split())
        
        ranked_chunks.append(RankedChunk(
            chunk_id=cid,
            content=chunk.content,
            word_count=word_count,
            start_line=chunk.start_line,
            end_line=chunk.end_line,
            dense_score=dense_scores.get(cid),
            dense_rank=dense_ranks.get(cid),
            lexical_score=lexical_scores.get(cid),
            lexical_rank=lexical_ranks.get(cid),
            rrf_score=rrf_score
        ))
        
    # Sort by rrf_score descending
    ranked_chunks.sort(key=lambda x: x.rrf_score, reverse=True)
    
    return ranked_chunks[:top_k]

def compute_similarity(embedding_a: List[float], embedding_b: List[float]) -> float:
    """
    Calculate cosine similarity between two embeddings.
    """
    if not embedding_a or not embedding_b:
        return 0.0
    
    dot_product = sum(a * b for a, b in zip(embedding_a, embedding_b))
    norm_a = math.sqrt(sum(a * a for a in embedding_a))
    norm_b = math.sqrt(sum(b * b for b in embedding_b))
    
    if norm_a == 0 or norm_b == 0:
        return 0.0
    
    return dot_product / (norm_a * norm_b)

def get_chunk_embeddings(chunk_ids: List[int], session: Session) -> Dict[int, List[float]]:
    """
    Batch fetch embeddings for given chunk IDs.
    Returns mapping of chunk_id -> embedding.
    """
    if not chunk_ids:
        return {}
    
    stmt = (
        select(Chunk.id, Chunk.embedding)
        .where(Chunk.id.in_(chunk_ids))
        .where(Chunk.embedding.isnot(None))
    )
    results = session.execute(stmt).all()
    
    return {row[0]: list(row[1]) for row in results}

def rerank_mmr(
    ranked_chunks: List[RankedChunk],
    embeddings: Dict[int, List[float]],
    lambda_param: float,
    top_n: int
) -> List[RankedChunk]:
    """
    Apply Maximal Marginal Relevance (MMR) re-ranking.
    MMR = lambda * relevance - (1 - lambda) * max_similarity_to_selected
    """
    if not ranked_chunks:
        return []
    
    # Filter to only those with embeddings
    candidates = [rc for rc in ranked_chunks if rc.chunk_id in embeddings]
    if not candidates:
        return []
        
    selected: List[RankedChunk] = []
    
    while len(selected) < top_n and candidates:
        best_mmr = -float('inf')
        best_candidate = None
        
        for cand in candidates:
            relevance = cand.rrf_score
            
            if not selected:
                mmr_score = relevance
            else:
                max_sim = max(
                    compute_similarity(embeddings[cand.chunk_id], embeddings[s.chunk_id])
                    for s in selected
                )
                mmr_score = lambda_param * relevance - (1 - lambda_param) * max_sim
            
            if mmr_score > best_mmr:
                best_mmr = mmr_score
                best_candidate = cand
        
        if best_candidate:
            best_candidate.mmr_score = float(best_mmr)
            selected.append(best_candidate)
            candidates.remove(best_candidate)
        else:
            break
            
    # Assign rank positions
    for i, rc in enumerate(selected):
        rc.rank_position = i + 1
        
    return selected

def rank_content_chunks(
    heading: HeadingInfo,
    session: Session,
    settings: SummarizeSettings
) -> List[RankedChunk]:
    """
    Main entry point to rank content-chunks of a heading.
    """
    # 1. Get child content-chunks (where parent_id = heading.chunk_id)
    # The spec says "parent_id = heading.chunk_id", but we should verify the level 
    # to be sure they are content chunks.
    stmt = (
        select(Chunk)
        .where(Chunk.parent_id == heading.chunk_id)
        .where(Chunk.dense_lexical_use == True)
    )
    content_chunks = session.execute(stmt).scalars().all()
    
    if not content_chunks:
        logger.warning(f"No content chunks found for heading {heading.chunk_id}")
        return []
    
    content_chunk_ids = [c.id for c in content_chunks]
    chunk_data_map = {c.id: c for c in content_chunks}
    
    # Get the parent chunk to access heading_breadcrumbs
    parent_chunk = session.get(Chunk, heading.chunk_id)
    breadcrumbs = parent_chunk.heading_breadcrumbs if parent_chunk else None
    
    # 2. Build search query
    query = build_search_query(breadcrumbs, heading.heading_title)
    
    # 3. Search dense
    dense_results = search_dense(
        query=query,
        content_chunk_ids=content_chunk_ids,
        session=session,
        top_k=settings.dense_top_k
    )
    
    # 4. Search lexical
    lexical_results = search_lexical(
        query=query,
        content_chunk_ids=content_chunk_ids,
        session=session,
        top_k=settings.lexical_top_k
    )
    
    # 5. Fuse with RRF
    fused_results = fuse_rrf(
        dense_results=dense_results,
        lexical_results=lexical_results,
        chunk_data_map=chunk_data_map,
        k=settings.rrf_k,
        top_k=settings.rrf_top_k
    )
    
    # 6. Apply MMR re-ranking
    # Fetch embeddings for top candidates from RRF
    fused_chunk_ids = [rc.chunk_id for rc in fused_results]
    embeddings = get_chunk_embeddings(fused_chunk_ids, session)
    
    final_results = rerank_mmr(
        ranked_chunks=fused_results,
        embeddings=embeddings,
        lambda_param=settings.mmr_lambda,
        top_n=settings.mmr_top_n
    )
    
    return final_results
