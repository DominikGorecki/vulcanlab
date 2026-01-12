"""
Result matching and reuse logic for deep research.

This module provides functions to identify existing research results that match
sub-questions and recommend reuse strategies based on similarity and quality.
"""

import re
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional

import numpy as np
from sqlalchemy import select
from sqlalchemy.orm import Session

from ..ai import create_embeddings
from ..data.models.collection_item import CollectionItem
from ..data.models.enums import CollectionItemType
from ..data.models.query import Query
from ..data.models.result import Result


def calculate_similarity(a: List[float], b: List[float]) -> float:
    """
    Compute cosine similarity between two embedding vectors.

    Args:
        a: First embedding vector.
        b: Second embedding vector.

    Returns:
        Cosine similarity as a float between -1.0 and 1.0.
    """
    a_arr = np.array(a)
    b_arr = np.array(b)
    
    norm_a = np.linalg.norm(a_arr)
    norm_b = np.linalg.norm(b_arr)
    
    if norm_a == 0 or norm_b == 0:
        return 0.0
        
    return float(np.dot(a_arr, b_arr) / (norm_a * norm_b))


def calculate_quality_score(result: Result) -> float:
    """
    Calculate a composite quality score (0.0 to 1.0) for a research result.

    Algorithm:
    - citation_density (40%): citations / word_count
    - freshness (20%): 1.0 - (days_old / 180)
    - completeness (15%): word_count / median_word_count
    - source_diversity (15%): unique_works_cited
    - model_quality (10%): 1.0 for high-quality models, 0.5 otherwise

    Args:
        result: The Result model instance to score.

    Returns:
        Weighted quality score between 0.0 and 1.0.
    """
    content = result.response_text or ""
    words = content.split()
    word_count = len(words)
    
    if word_count == 0:
        return 0.0

    # 1. citation_density (40%)
    # Heuristic: count [Author Year] patterns
    citation_pattern = r'\[[A-Za-z\s]+(?:\set\sal\.)?\s\d{4}\]'
    citations = re.findall(citation_pattern, content)
    citation_count = len(citations)
    # Assume 1 citation per 50 words is 1.0 density (generous)
    citation_density = min(citation_count / (word_count / 50.0) if word_count > 0 else 0, 1.0)

    # 2. freshness (20%)
    # freshness = 1.0 - (days_old / 180) capped at 0
    now = datetime.now(timezone.utc)
    created_at = result.created_at
    if created_at.tzinfo is None:
        created_at = created_at.replace(tzinfo=timezone.utc)
    
    days_old = (now - created_at).days
    freshness = max(0.0, 1.0 - (days_old / 180.0))

    # 3. completeness (15%)
    # word_count / median_word_count. Assume median is 1000 words.
    median_word_count = 1000.0
    completeness = min(word_count / median_word_count, 1.0)

    # 4. source_diversity (15%)
    # unique_works_cited. Assume 5+ unique sources is 1.0 diversity.
    unique_citations = set(citations)
    source_diversity = min(len(unique_citations) / 5.0, 1.0)

    # 5. model_quality (10%)
    # 1.0 if high-quality model else 0.5
    model_quality = 0.5
    if result.model:
        model_name = result.model.name.lower()
        # Common high-quality model keywords
        if any(hq in model_name for hq in ["gpt-4", "o1", "pro", "ultra", "claude-3-5"]):
            model_quality = 1.0

    score = (
        citation_density * 0.40 +
        freshness * 0.20 +
        completeness * 0.15 +
        source_diversity * 0.15 +
        model_quality * 0.10
    )
    
    return float(max(0.0, min(1.0, score)))


def recommend_reuse_strategy(matched_results: List[Dict[str, Any]]) -> str:
    """
    Recommend a reuse strategy based on matched results.

    Decision logic:
    - 0 high-quality (score > 0.75) -> "new_generation"
    - 1 high-quality, similarity > 0.90 -> "exact_reuse"
    - 1 high-quality, similarity 0.85-0.90 -> "partial_reuse"
    - 2-3 high-quality -> "ensemble"
    - 4+ high-quality -> "ensemble" (with diversity sampling)

    Args:
        matched_results: List of dicts with 'similarity' and 'quality_score'.

    Returns:
        Strategy string: "new_generation", "exact_reuse", "partial_reuse", or "ensemble".
    """
    high_quality_results = [r for r in matched_results if r['quality_score'] > 0.75]
    count = len(high_quality_results)

    if count == 0:
        return "new_generation"
    
    if count == 1:
        best = high_quality_results[0]
        if best['similarity'] > 0.90:
            return "exact_reuse"
        elif best['similarity'] > 0.85:
            return "partial_reuse"
    
    # For 2 or more high-quality results
    return "ensemble"


def match_results_for_question(
    question_text: str,
    collection_id: int,
    session: Session
) -> List[Dict[str, Any]]:
    """
    Identify existing research results that match a sub-question.

    Args:
        question_text: The research sub-question to match against.
        collection_id: ID of the collection to search within.
        session: Database session.

    Returns:
        List of matching result dictionaries sorted by quality_score DESC.
        Each dict contains: {result_id, similarity, quality_score, result_preview, created_at}
    """
    # Generate embedding for question_text
    embeddings_model = create_embeddings()
    question_embedding = embeddings_model.embed_query(question_text)

    # Query all research_result items in the collection
    items_query = select(CollectionItem).where(
        CollectionItem.collection_id == collection_id,
        CollectionItem.item_type == CollectionItemType.RESEARCH_RESULT
    )
    items = session.execute(items_query).scalars().all()

    matched_results = []
    for item in items:
        # Parse result_id from link: /rag/{query_id}/results/{result_id}
        match = re.search(r"/results/(\d+)", item.link)
        if not match:
            continue
        
        result_id = int(match.group(1))
        result = session.get(Result, result_id)
        if not result:
            continue
        
        query = session.get(Query, result.query_id)
        if not query:
            continue
        
        # Get or generate embedding for original query
        result_embedding = query.embedding_original
        if result_embedding is None:
            # Generate and cache embedding if missing
            result_embedding = embeddings_model.embed_query(query.original_query)
            query.embedding_original = result_embedding
            query.vector_status = "vec"
            session.add(query)
            session.flush()

        similarity = calculate_similarity(question_embedding, result_embedding)

        # Threshold from R7: similarity > 0.85
        if similarity > 0.85:
            quality_score = calculate_quality_score(result)
            preview = result.response_text[:200] + "..." if len(result.response_text or "") > 200 else (result.response_text or "")
            
            matched_results.append({
                "result_id": result.id,
                "similarity": similarity,
                "quality_score": quality_score,
                "result_preview": preview,
                "created_at": result.created_at
            })

    # Sort by quality_score DESC as per requirements
    matched_results.sort(key=lambda x: x['quality_score'], reverse=True)
    
    return matched_results
