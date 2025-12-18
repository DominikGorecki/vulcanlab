"""
Retrieval module for dense + lexical search with RRF fusion and BGE reranking.

This module implements the full retrieval pipeline:
1. Dense retrieval (pgvector similarity)
2. Lexical retrieval (PostgreSQL full-text search)
3. RRF fusion
4. BGE reranking with entity/intent bias
5. Final selection and storage

Usage:
    from vulcanlab.retrieval.retrieve import retrieve
    result = retrieve(query_id=1, verbose=True)
"""

from dataclasses import dataclass, field
from datetime import datetime
from pathlib import Path
import json

import numpy as np
import torch
from sqlalchemy import text
from transformers import AutoModelForSequenceClassification, AutoTokenizer

from vulcanlab.data.database import get_session
from vulcanlab.data.models import Chunk, Query, Work
from vulcanlab.utils.file_utils import compute_file_hash, get_path_resolver
from vulcanlab.utils.rag_config_loader import get_default_config, get_config_by_name
from vulcanlab.config.app_config import load_config


# Initialize path resolver
resolver = get_path_resolver()





@dataclass
class RetrievedChunk:
    """A retrieved chunk with all metadata and scores."""

    id: int
    parent_id: int | None
    work_id: int
    content: str
    enriched_content: str
    start_line: int
    end_line: int
    level: str
    heading_breadcrumbs: str | None = None
    dense_rank: int | None = None
    lexical_rank: int | None = None
    rrf_score: float = 0.0
    rerank_score: float = 0.0
    entity_boost: float = 0.0
    final_score: float = 0.0
    # Embedding for MMR diversity (not persisted, used internally)
    _embedding: np.ndarray | None = field(default=None, repr=False)


@dataclass
class RetrievalResult:
    """Result of the retrieval operation."""

    query_id: int
    total_dense_candidates: int
    total_lexical_candidates: int
    rrf_candidates: int
    final_count: int
    chunks: list[RetrievedChunk]


# Default parameters
DEFAULT_DENSE_LIMIT = 19
DEFAULT_LEXICAL_LIMIT = 5
DEFAULT_RRF_K = 50                  #60
DEFAULT_TOP_K_RRF = 75              #60
DEFAULT_TOP_N_FINAL = 17
DEFAULT_ENTITY_BOOST = 0.05   #0.05
DEFAULT_MIN_CONTENT_LENGTH = 750    # characters (for enrichment)
DEFAULT_ENRICH_LINES_ABOVE = 0      # lines to add above chunk when enriching
DEFAULT_ENRICH_LINES_BELOW = 13     # lines to add below chunk when enriching
DEFAULT_MIN_WORD_COUNT = 150         # minimum words in chunk.content to be included
DEFAULT_MIN_CHAR_COUNT = 250        # minimum characters in chunk.content to be included
# Default MMR parameters
DEFAULT_MMR_LAMBDA = 0.7  #0.7 Balance between relevance (1.0) and diversity (0.0)


def _serialize_chunk_for_log(chunk: RetrievedChunk) -> dict:
    """Serialize a RetrievedChunk to a JSON-serializable dict."""
    return {
        "id": chunk.id,
        "parent_id": chunk.parent_id,
        "work_id": chunk.work_id,
        "content": chunk.content,
        "enriched_content": chunk.enriched_content,
        "start_line": chunk.start_line,
        "end_line": chunk.end_line,
        "level": chunk.level,
        "heading_breadcrumbs": chunk.heading_breadcrumbs,
        "dense_rank": chunk.dense_rank,
        "lexical_rank": chunk.lexical_rank,
        "rrf_score": chunk.rrf_score,
        "rerank_score": chunk.rerank_score,
        "entity_boost": chunk.entity_boost,
        "final_score": chunk.final_score,
    }


def _log_retrieval_stage(
    query_id: int,
    stage: str,
    data: dict,
    log_data: dict
) -> None:
    """Log a retrieval stage to the log_data dict."""
    if not load_config().logging.enabled:
        return
    
    log_data["stages"][stage] = {
        "timestamp": datetime.now().isoformat(),
        **data
    }


def _save_retrieval_log(query_id: int, log_data: dict) -> None:
    """Save retrieval log to JSON file."""
    config = load_config()
    if not config.logging.enabled:
        return
    
    log_dir = Path(config.logging.log_dir)
    log_dir.mkdir(exist_ok=True, parents=True)
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    log_file = log_dir / f"retrieve_query_{query_id}_{timestamp}.json"
    
    with open(log_file, 'w', encoding='utf-8') as f:
        json.dump(log_data, f, indent=2, ensure_ascii=False)


def _meets_minimum_requirements(
    content: str,
    min_word_count: int = DEFAULT_MIN_WORD_COUNT,
    min_char_count: int = DEFAULT_MIN_CHAR_COUNT
) -> bool:
    """Check if chunk content meets minimum length requirements.

    Args:
        content: The chunk content to check
        min_word_count: Minimum number of words required (0 to disable)
        min_char_count: Minimum number of characters required (0 to disable)

    Returns:
        True if content meets both requirements, False otherwise
    """
    if not content or not content.strip():
        return False

    # Check character count (if enabled)
    if min_char_count > 0 and len(content) < min_char_count:
        return False

    # Check word count (if enabled)
    if min_word_count > 0:
        word_count = len(content.split())
        if word_count < min_word_count:
            return False

    return True


def _dense_search(
    session,
    embedding: list,
    limit: int = DEFAULT_DENSE_LIMIT,
    sentence_filter_enabled: bool = False,
    min_sentence_count: int = 5
) -> list[tuple[int, int]]:
    """Perform dense vector search.

    Args:
        session: Database session
        embedding: Query embedding vector
        limit: Maximum number of results
        sentence_filter_enabled: Whether to filter by sentence count
        min_sentence_count: Minimum sentence count threshold (if filter enabled)

    Returns list of (chunk_id, rank) tuples.
    """
    # Convert to list if numpy array, then format as PostgreSQL vector literal
    if hasattr(embedding, 'tolist'):
        embedding = embedding.tolist()
    embedding_str = '[' + ','.join(str(x) for x in embedding) + ']'

    # Build WHERE clause conditionally
    where_clauses = ["embedding IS NOT NULL"]
    params = {"embedding": embedding_str, "limit": limit}

    if sentence_filter_enabled:
        where_clauses.append("(sentence_count IS NOT NULL AND sentence_count >= :min_sentence_count)")
        params["min_sentence_count"] = min_sentence_count

    where_clause = " AND ".join(where_clauses)

    result = session.execute(
        text(f"""
            SELECT id
            FROM chunks
            WHERE {where_clause}
            ORDER BY embedding <=> :embedding
            LIMIT :limit
        """),
        params
    )
    return [(row[0], i + 1) for i, row in enumerate(result.fetchall())]


def _lexical_search(
    session,
    query_text: str,
    limit: int = DEFAULT_LEXICAL_LIMIT,
    sentence_filter_enabled: bool = False,
    min_sentence_count: int = 5
) -> list[tuple[int, int]]:
    """Perform lexical full-text search with phrase support.

    Uses websearch_to_tsquery for better phrase handling:
    - Quoted phrases ("schema therapy") require adjacent words
    - Negation (-anxiety) excludes matching chunks
    - OR logic (CBT or DBT) matches either term

    Uses ts_rank_cd which considers document structure and proximity,
    providing better ranking than basic ts_rank.

    Args:
        session: Database session
        query_text: Query text for full-text search
        limit: Maximum number of results
        sentence_filter_enabled: Whether to filter by sentence count
        min_sentence_count: Minimum sentence count threshold (if filter enabled)

    Returns list of (chunk_id, rank) tuples.
    """
    # Use websearch_to_tsquery for phrase and negation support
    # ts_rank_cd considers cover density (proximity) for better ranking

    # Build WHERE clause conditionally
    where_clauses = [
        "content_tsvector @@ websearch_to_tsquery('english', :query)",
        "vector_status = 'vec'"
    ]
    params = {"query": query_text, "limit": limit}

    if sentence_filter_enabled:
        where_clauses.append("(sentence_count IS NOT NULL AND sentence_count >= :min_sentence_count)")
        params["min_sentence_count"] = min_sentence_count

    where_clause = " AND ".join(where_clauses)

    result = session.execute(
        text(f"""
            SELECT id
            FROM chunks
            WHERE {where_clause}
            ORDER BY ts_rank_cd(content_tsvector, websearch_to_tsquery('english', :query)) DESC
            LIMIT :limit
        """),
        params
    )
    return [(row[0], i + 1) for i, row in enumerate(result.fetchall())]


def _compute_rrf_scores(
    results_list: list[list[tuple[int, int]]],
    k: int = DEFAULT_RRF_K
) -> dict[int, float]:
    """Compute RRF scores from multiple ranked lists.

    Args:
        results_list: List of [(chunk_id, rank), ...] for each query
        k: RRF constant (default 60)

    Returns:
        Dict mapping chunk_id to RRF score
    """
    scores = {}
    for results in results_list:
        for chunk_id, rank in results:
            if chunk_id not in scores:
                scores[chunk_id] = 0.0
            scores[chunk_id] += 1.0 / (k + rank)
    return scores


def _enrich_content(
    chunk: Chunk,
    work: Work,
    lines_above: int = DEFAULT_ENRICH_LINES_ABOVE,
    lines_below: int = DEFAULT_ENRICH_LINES_BELOW,
    min_length: int = DEFAULT_MIN_CONTENT_LENGTH
) -> str:
    """Enrich short chunks with surrounding context from markdown file.

    Args:
        chunk: The chunk to potentially enrich
        work: The work containing markdown_path
        lines_above: Number of lines to add above chunk (default 0)
        lines_below: Number of lines to add below chunk (default 13)
        min_length: Minimum content length before enrichment (default 350)

    Returns:
        Enriched content or original content
    """
    if len(chunk.content) >= min_length:
        return chunk.content

    # Check if work has sanitized markdown file
    if not work.files or "sanitized" not in work.files:
        return chunk.content

    markdown_path = resolver.resolve_work_path(work, "sanitized")
    if not markdown_path.exists():
        return chunk.content

    # Verify file hasn't changed
    if work.content_hash:
        current_hash = compute_file_hash(markdown_path)
        if current_hash != work.content_hash:
            return chunk.content

    # Read markdown file
    try:
        lines = markdown_path.read_text(encoding='utf-8').splitlines()
    except Exception:
        return chunk.content

    # Get context lines (0-indexed)
    start_idx = max(0, chunk.start_line - 1 - lines_above)
    end_idx = min(len(lines), chunk.end_line + lines_below)

    # Build enriched content
    above_lines = lines[start_idx:chunk.start_line - 1] if lines_above > 0 and chunk.start_line > 1 else []
    below_lines = lines[chunk.end_line:end_idx] if lines_below > 0 and chunk.end_line < len(lines) else []

    parts = []
    if above_lines:
        parts.append('\n'.join(above_lines))
        parts.append('')  # Blank line
    parts.append(chunk.content)
    if below_lines:
        parts.append('')  # Blank line
        parts.append('\n'.join(below_lines))

    return '\n'.join(parts)


def _load_reranker():
    """Load BGE reranker model with GPU fallback to CPU."""
    model_name = "BAAI/bge-reranker-large"

    # Try GPU first
    device = "cuda" if torch.cuda.is_available() else "cpu"

    tokenizer = AutoTokenizer.from_pretrained(model_name)

    if device == "cuda":
        model = AutoModelForSequenceClassification.from_pretrained(
            model_name,
            torch_dtype=torch.float16
        ).to(device)
    else:
        model = AutoModelForSequenceClassification.from_pretrained(model_name).to(device)

    model.eval()
    return tokenizer, model, device


def _rerank_chunks(
    query: str,
    chunks: list[RetrievedChunk],
    batch_size: int = 8,
    max_length: int = 512
) -> list[RetrievedChunk]:
    """Rerank chunks using BGE reranker.

    Args:
        query: Original query text
        chunks: List of chunks to rerank
        batch_size: Batch size for inference
        max_length: Maximum token length

    Returns:
        Chunks with updated rerank_score
    """
    if not chunks:
        return chunks

    tokenizer, model, device = _load_reranker()

    # Prepare pairs
    pairs = [(query, chunk.enriched_content) for chunk in chunks]

    # Process in batches
    scores = []
    for i in range(0, len(pairs), batch_size):
        batch = pairs[i:i + batch_size]

        inputs = tokenizer(
            batch,
            padding=True,
            truncation=True,
            max_length=max_length,
            return_tensors="pt"
        ).to(device)

        with torch.no_grad():
            outputs = model(**inputs)
            batch_scores = outputs.logits.squeeze(-1).cpu().tolist()

            # Handle single item case
            if isinstance(batch_scores, float):
                batch_scores = [batch_scores]

            scores.extend(batch_scores)

    # Update chunks with scores
    for chunk, score in zip(chunks, scores):
        chunk.rerank_score = score

    return chunks


def _apply_entity_bias(
    chunks: list[RetrievedChunk],
    entities: list[str],
    boost: float = DEFAULT_ENTITY_BOOST
) -> list[RetrievedChunk]:
    """Apply entity boost to rerank scores.

    Args:
        chunks: Chunks with rerank scores
        entities: List of entities to match
        boost: Score boost per entity match

    Returns:
        Chunks with updated entity_boost and final_score
    """
    if not entities:
        for chunk in chunks:
            chunk.final_score = chunk.rerank_score
        return chunks

    # Normalize entities for matching
    normalized_entities = [e.lower() for e in entities]

    for chunk in chunks:
        content_lower = chunk.enriched_content.lower()

        # Count entity matches
        matches = sum(1 for entity in normalized_entities if entity in content_lower)

        chunk.entity_boost = matches * boost
        chunk.final_score = chunk.rerank_score + chunk.entity_boost

    return chunks


# Intent preferences: level preferences and length preferences per intent type
# Each intent maps to preferred heading levels and content length category
INTENT_PREFERENCES = {
    "DEFINITION": {
        "preferred_levels": ["H2", "H3"],
        "length_preference": "short",  # < 500 chars
        "level_boost": 0.03,
        "length_boost": 0.01,
    },
    "MECHANISM": {
        "preferred_levels": ["H3", "H4", "chunk"],
        "length_preference": "long",  # > 800 chars
        "level_boost": 0.02,
        "length_boost": 0.01,
    },
    "COMPARISON": {
        "preferred_levels": ["H2", "H3"],
        "length_preference": "medium",  # 400-900 chars
        "level_boost": 0.02,
        "length_boost": 0.01,
    },
    "APPLICATION": {
        "preferred_levels": ["H4", "chunk", "sentence"],
        "length_preference": "medium",
        "level_boost": 0.02,
        "length_boost": 0.01,
    },
    "STUDY_DETAIL": {
        "preferred_levels": ["H4", "chunk"],
        "length_preference": "long",
        "level_boost": 0.03,
        "length_boost": 0.01,
    },
    "CRITIQUE": {
        "preferred_levels": ["H3", "H4"],
        "length_preference": "medium",
        "level_boost": 0.02,
        "length_boost": 0.01,
    },
}


def _apply_intent_bias(
    chunks: list[RetrievedChunk],
    intent: str | None
) -> list[RetrievedChunk]:
    """Apply intent-based bias to scores.

    Different intents favor different chunk characteristics:
    - DEFINITION: prefer shorter chunks at H2/H3 level
    - MECHANISM: prefer longer explanatory chunks at H3/H4/chunk level
    - COMPARISON: prefer H2/H3 chunks with medium length
    - APPLICATION: prefer practical H4/chunk/sentence with medium length
    - STUDY_DETAIL: prefer longer H4/chunk with methodology details
    - CRITIQUE: prefer H3/H4 chunks with evaluative content

    Args:
        chunks: Chunks with current final_score set
        intent: Query intent type (DEFINITION, MECHANISM, etc.)

    Returns:
        Chunks with final_score adjusted based on intent preferences
    """
    if not intent or not chunks:
        return chunks

    # Get preferences for this intent
    prefs = INTENT_PREFERENCES.get(intent.upper())
    if not prefs:
        return chunks

    for chunk in chunks:
        boost = 0.0

        # Level preference boost
        if chunk.level in prefs["preferred_levels"]:
            boost += prefs["level_boost"]

        # Length preference boost (based on enriched_content)
        content_len = len(chunk.enriched_content)
        length_pref = prefs["length_preference"]

        if length_pref == "short" and content_len < 500:
            boost += prefs["length_boost"]
        elif length_pref == "long" and content_len > 800:
            boost += prefs["length_boost"]
        elif length_pref == "medium" and 400 <= content_len <= 900:
            boost += prefs["length_boost"]

        # Apply the boost to final_score
        chunk.final_score += boost

    return chunks




def _cosine_similarity(vec1: np.ndarray, vec2: np.ndarray) -> float:
    """Compute cosine similarity between two vectors.

    Args:
        vec1: First vector
        vec2: Second vector

    Returns:
        Cosine similarity score between -1 and 1
    """
    norm1 = np.linalg.norm(vec1)
    norm2 = np.linalg.norm(vec2)
    if norm1 == 0 or norm2 == 0:
        return 0.0
    return float(np.dot(vec1, vec2) / (norm1 * norm2))


def _jaccard_similarity(text1: str, text2: str) -> float:
    """Compute Jaccard similarity based on word overlap.

    Used as fallback when embeddings are not available.

    Args:
        text1: First text
        text2: Second text

    Returns:
        Jaccard similarity score between 0 and 1
    """
    words1 = set(text1.lower().split())
    words2 = set(text2.lower().split())
    if not words1 or not words2:
        return 0.0
    intersection = len(words1 & words2)
    union = len(words1 | words2)
    return intersection / union if union > 0 else 0.0


def _compute_chunk_similarity(
    chunk1: RetrievedChunk,
    chunk2: RetrievedChunk
) -> float:
    """Compute similarity between two chunks.

    Uses embedding cosine similarity if both chunks have embeddings,
    otherwise falls back to Jaccard word overlap.

    Args:
        chunk1: First chunk
        chunk2: Second chunk

    Returns:
        Similarity score between 0 and 1
    """
    # Use embedding similarity if available
    if chunk1._embedding is not None and chunk2._embedding is not None:
        # Cosine similarity can be negative; normalize to [0, 1]
        cos_sim = _cosine_similarity(chunk1._embedding, chunk2._embedding)
        return (cos_sim + 1) / 2  # Map [-1, 1] to [0, 1]

    # Fallback to Jaccard
    return _jaccard_similarity(chunk1.enriched_content, chunk2.enriched_content)


def _apply_mmr_diversity(
    chunks: list[RetrievedChunk],
    top_n: int,
    lambda_param: float = DEFAULT_MMR_LAMBDA
) -> list[RetrievedChunk]:
    """Apply Maximal Marginal Relevance for diverse chunk selection.

    MMR balances relevance and diversity by iteratively selecting chunks
    that maximize: λ * relevance - (1-λ) * max_similarity_to_selected

    Args:
        chunks: Chunks sorted by final_score (descending)
        top_n: Number of chunks to select
        lambda_param: Balance parameter (0.7 = 70% relevance, 30% diversity)

    Returns:
        Selected chunks with diverse content
    """
    if not chunks or len(chunks) <= top_n:
        return chunks

    # Normalize scores to [0, 1] for fair comparison with similarity
    scores = [c.final_score for c in chunks]
    min_score = min(scores)
    max_score = max(scores)
    score_range = max_score - min_score if max_score != min_score else 1.0

    def normalized_score(chunk: RetrievedChunk) -> float:
        return (chunk.final_score - min_score) / score_range

    # Start with the highest-scoring chunk
    selected = [chunks[0]]
    remaining = list(chunks[1:])

    while len(selected) < top_n and remaining:
        best_idx = -1
        best_mmr = float('-inf')

        for i, candidate in enumerate(remaining):
            # Relevance component (normalized)
            relevance = normalized_score(candidate)

            # Diversity component: max similarity to any selected chunk
            max_sim = max(
                _compute_chunk_similarity(candidate, s)
                for s in selected
            )

            # MMR score
            mmr_score = lambda_param * relevance - (1 - lambda_param) * max_sim

            if mmr_score > best_mmr:
                best_mmr = mmr_score
                best_idx = i

        if best_idx >= 0:
            selected.append(remaining.pop(best_idx))

    return selected


def retrieve(
    query_id: int,
    dense_limit: int | None = None,
    lexical_limit: int | None = None,
    rrf_k: int | None = None,
    top_k_rrf: int | None = None,
    top_n_final: int | None = None,
    entity_boost: float | None = None,
    min_word_count: int | None = None,
    min_char_count: int | None = None,
    config_preset: str | None = None,
    verbose: bool = False
) -> RetrievalResult:
    """Perform full retrieval pipeline for a query.

    Args:
        query_id: ID of the Query in the database
        dense_limit: Max results per dense query. If None, uses config.
        lexical_limit: Max results per lexical query. If None, uses config.
        rrf_k: RRF constant. If None, uses config.
        top_k_rrf: Top candidates after RRF. If None, uses config.
        top_n_final: Final number of results. If None, uses config.
        entity_boost: Score boost per entity match. If None, uses config.
        min_word_count: Minimum words in chunk content. If None, uses config.
        min_char_count: Minimum characters in chunk content. If None, uses config.
        config_preset: Name of RAG config preset to use. If None, uses default.
        verbose: Print progress information

    Returns:
        RetrievalResult with retrieved chunks

    Raises:
        ValueError: If query not found or not vectorized, or if config preset not found
    """
    # Load configuration
    if config_preset:
        config = get_config_by_name(config_preset)
    else:
        config = get_default_config()

    retrieval_params = config["retrieval"]

    # Use provided parameters or fall back to config
    dense_limit = dense_limit if dense_limit is not None else retrieval_params["dense_limit"]
    lexical_limit = lexical_limit if lexical_limit is not None else retrieval_params["lexical_limit"]
    rrf_k = rrf_k if rrf_k is not None else retrieval_params["rrf_k"]
    top_k_rrf = top_k_rrf if top_k_rrf is not None else retrieval_params["top_k_rrf"]
    top_n_final = top_n_final if top_n_final is not None else retrieval_params["top_n_final"]
    entity_boost = entity_boost if entity_boost is not None else retrieval_params["entity_boost"]
    min_word_count = min_word_count if min_word_count is not None else retrieval_params["min_word_count"]
    min_char_count = min_char_count if min_char_count is not None else retrieval_params["min_char_count"]
    min_content_length = retrieval_params["min_content_length"]
    enrich_lines_above = retrieval_params["enrich_lines_above"]
    enrich_lines_below = retrieval_params["enrich_lines_below"]
    mmr_lambda = retrieval_params["mmr_lambda"]
    reranker_batch_size = retrieval_params["reranker_batch_size"]
    reranker_max_length = retrieval_params["reranker_max_length"]

    # Sentence filter settings
    min_sentence_filter_enabled = retrieval_params.get("min_sentence_filter_enabled", False)
    min_sentence_count = retrieval_params.get("min_sentence_count", 5)

    if verbose:
        print(f"Using RAG config preset: {config_preset or 'default'}")
        print(f"  dense_limit={dense_limit}, lexical_limit={lexical_limit}, top_n_final={top_n_final}")
        if min_sentence_filter_enabled:
            print(f"  Sentence filter active: min_count={min_sentence_count}")
        else:
            print(f"  Sentence filter disabled")

    # Initialize logging
    log_data = {
        "query_id": query_id,
        "timestamp": datetime.now().isoformat(),
        "config": {
            "preset": config_preset or "default",
            "dense_limit": dense_limit,
            "lexical_limit": lexical_limit,
            "rrf_k": rrf_k,
            "top_k_rrf": top_k_rrf,
            "top_n_final": top_n_final,
            "entity_boost": entity_boost,
            "min_word_count": min_word_count,
            "min_char_count": min_char_count,
            "mmr_lambda": mmr_lambda,
            "min_sentence_filter_enabled": min_sentence_filter_enabled,
            "min_sentence_count": min_sentence_count,
        },
        "stages": {}
    }

    with get_session() as session:
        # Fetch query
        query = session.query(Query).filter(Query.id == query_id).first()
        if not query:
            raise ValueError(f"Query with ID {query_id} not found")

        if query.vector_status != 'vec':
            raise ValueError(f"Query {query_id} has not been vectorized (status: {query.vector_status})")

        if verbose:
            print(f"Retrieving for query {query_id}: {query.original_query[:50]}...")

        # Log query info
        log_data["query"] = {
            "original_query": query.original_query,
            "intent": query.intent,
            "entities": query.entities or [],
        }

        # Collect all embeddings
        embeddings = []
        query_texts = []

        # Original query
        if query.embedding_original is not None:
            embeddings.append(query.embedding_original)
        query_texts.append(query.original_query)

        # MQE queries
        mqe_embeddings = query.embeddings_mqe or []
        mqe_texts = query.expanded_queries or []
        embeddings.extend(mqe_embeddings)
        query_texts.extend(mqe_texts)

        # HyDE (only for dense, not lexical)
        if query.embedding_hyde is not None:
            embeddings.append(query.embedding_hyde)

        if verbose:
            print(f"  Using {len(embeddings)} embeddings for dense search")
            print(f"  Using {len(query_texts)} queries for lexical search")

        # Dense retrieval
        dense_results = []
        num_original = 1 if query.embedding_original is not None else 0
        num_mqe = len(mqe_embeddings)
        for idx, emb in enumerate(embeddings):
            results = _dense_search(
                session, emb, dense_limit,
                sentence_filter_enabled=min_sentence_filter_enabled,
                min_sentence_count=min_sentence_count
            )
            dense_results.append(results)
            if load_config().logging.enabled:
                # Determine query type based on position
                if idx == 0 and num_original > 0:
                    query_type = "original"
                elif idx < num_original + num_mqe:
                    query_type = "mqe"
                else:
                    query_type = "hyde"
                
                log_data.setdefault("dense_queries", []).append({
                    "query_index": idx,
                    "query_type": query_type,
                    "results": [{"chunk_id": chunk_id, "rank": rank} for chunk_id, rank in results]
                })

        total_dense = sum(len(r) for r in dense_results)
        if verbose:
            print(f"  Dense retrieval: {total_dense} candidates")
        
        _log_retrieval_stage(query_id, "dense_retrieval", {
            "total_candidates": total_dense,
            "num_queries": len(embeddings),
            "all_chunk_ids": list(set(chunk_id for results in dense_results for chunk_id, _ in results))
        }, log_data)

        # Lexical retrieval (not using HyDE)
        lexical_results = []
        for idx, text in enumerate(query_texts):
            results = _lexical_search(
                session, text, lexical_limit,
                sentence_filter_enabled=min_sentence_filter_enabled,
                min_sentence_count=min_sentence_count
            )
            lexical_results.append(results)
            if load_config().logging.enabled:
                log_data.setdefault("lexical_queries", []).append({
                    "query_index": idx,
                    "query_text": text[:200],  # Truncate for logging
                    "results": [{"chunk_id": chunk_id, "rank": rank} for chunk_id, rank in results]
                })

        total_lexical = sum(len(r) for r in lexical_results)
        if verbose:
            print(f"  Lexical retrieval: {total_lexical} candidates")
        
        _log_retrieval_stage(query_id, "lexical_retrieval", {
            "total_candidates": total_lexical,
            "num_queries": len(query_texts),
            "all_chunk_ids": list(set(chunk_id for results in lexical_results for chunk_id, _ in results))
        }, log_data)

        # RRF fusion
        all_results = dense_results + lexical_results
        rrf_scores = _compute_rrf_scores(all_results, rrf_k)

        # Sort by RRF score and take top_k_rrf
        sorted_ids = sorted(rrf_scores.keys(), key=lambda x: rrf_scores[x], reverse=True)
        top_ids = sorted_ids[:top_k_rrf]

        if verbose:
            print(f"  RRF fusion: {len(rrf_scores)} unique candidates -> top {len(top_ids)}")
        
        _log_retrieval_stage(query_id, "rrf_fusion", {
            "unique_candidates": len(rrf_scores),
            "top_k_rrf": top_k_rrf,
            "selected_chunk_ids": top_ids,
            "rrf_scores": {str(chunk_id): score for chunk_id, score in rrf_scores.items() if chunk_id in top_ids}
        }, log_data)

        # Fetch chunk data
        chunks_data = session.query(Chunk).filter(Chunk.id.in_(top_ids)).all()

        # Filter out chunks that don't meet minimum requirements
        filtered_chunks = [
            c for c in chunks_data
            if _meets_minimum_requirements(c.content, min_word_count, min_char_count)
        ]
        filtered_out_ids = [c.id for c in chunks_data if c not in filtered_chunks]

        if verbose and len(filtered_chunks) < len(chunks_data):
            filtered_count = len(chunks_data) - len(filtered_chunks)
            print(f"  Filtered out {filtered_count} chunks below minimum length requirements")
        
        _log_retrieval_stage(query_id, "filtering", {
            "before_count": len(chunks_data),
            "after_count": len(filtered_chunks),
            "filtered_out_chunk_ids": filtered_out_ids,
            "min_word_count": min_word_count,
            "min_char_count": min_char_count
        }, log_data)

        # Build maps with embeddings for MMR diversity
        chunks_map = {c.id: c for c in filtered_chunks}
        embeddings_map = {c.id: c.embedding for c in filtered_chunks}

        # Get work data for enrichment
        work_ids = {c.work_id for c in filtered_chunks}
        works = session.query(Work).filter(Work.id.in_(work_ids)).all()
        works_map = {w.id: w for w in works}

        # Build RetrievedChunk objects (with embeddings for MMR)
        retrieved_chunks = []
        for chunk_id in top_ids:
            if chunk_id not in chunks_map:
                continue

            chunk = chunks_map[chunk_id]
            work = works_map.get(chunk.work_id)

            # Enrich content
            enriched = _enrich_content(
                chunk, work,
                lines_above=enrich_lines_above,
                lines_below=enrich_lines_below,
                min_length=min_content_length
            ) if work else chunk.content

            # Option B: Keep breadcrumbs separate, reranker sees content only
            # Breadcrumbs are stored in heading_breadcrumbs field and saved context

            # Get embedding as numpy array for MMR (if available)
            embedding = embeddings_map.get(chunk_id)
            np_embedding = None
            if embedding is not None:
                np_embedding = np.array(embedding, dtype=np.float32)

            retrieved_chunks.append(RetrievedChunk(
                id=chunk.id,
                parent_id=chunk.parent_id,
                work_id=chunk.work_id,
                content=chunk.content,
                enriched_content=enriched,
                start_line=chunk.start_line,
                end_line=chunk.end_line,
                level=chunk.level,
                heading_breadcrumbs=chunk.heading_breadcrumbs,
                rrf_score=rrf_scores[chunk_id],
                _embedding=np_embedding
            ))

        if verbose:
            print(f"  Reranking {len(retrieved_chunks)} candidates...")

        # BGE reranking
        retrieved_chunks = _rerank_chunks(
            query.original_query,
            retrieved_chunks,
            batch_size=reranker_batch_size,
            max_length=reranker_max_length
        )
        
        _log_retrieval_stage(query_id, "reranking", {
            "num_candidates": len(retrieved_chunks),
            "chunks": [_serialize_chunk_for_log(chunk) for chunk in retrieved_chunks]
        }, log_data)

        # Apply entity bias
        entities = query.entities or []
        retrieved_chunks = _apply_entity_bias(retrieved_chunks, entities, entity_boost)
        
        _log_retrieval_stage(query_id, "entity_bias", {
            "entities": entities,
            "boost_per_entity": entity_boost,
            "chunks": [_serialize_chunk_for_log(chunk) for chunk in retrieved_chunks]
        }, log_data)

        # Apply intent bias
        retrieved_chunks = _apply_intent_bias(retrieved_chunks, query.intent)
        
        _log_retrieval_stage(query_id, "intent_bias", {
            "intent": query.intent,
            "chunks": [_serialize_chunk_for_log(chunk) for chunk in retrieved_chunks]
        }, log_data)

        # Sort by final_score before MMR
        retrieved_chunks.sort(key=lambda x: x.final_score, reverse=True)

        # Apply MMR diversity for final selection
        if verbose:
            print(f"  Applying MMR diversity selection...")
        
        chunks_before_mmr = [_serialize_chunk_for_log(chunk) for chunk in retrieved_chunks]
        final_chunks = _apply_mmr_diversity(retrieved_chunks, top_n_final, lambda_param=mmr_lambda)
        
        _log_retrieval_stage(query_id, "mmr_diversity", {
            "lambda": mmr_lambda,
            "top_n": top_n_final,
            "before_count": len(retrieved_chunks),
            "after_count": len(final_chunks),
            "selected_chunk_ids": [chunk.id for chunk in final_chunks],
            "chunks_before_mmr": chunks_before_mmr,
            "final_chunks": [_serialize_chunk_for_log(chunk) for chunk in final_chunks]
        }, log_data)

        if verbose:
            print(f"  Final selection: {len(final_chunks)} chunks (with diversity)")

        # Save to database
        context_data = []
        for chunk in final_chunks:
            context_data.append({
                "id": chunk.id,
                "parent_id": chunk.parent_id,
                "work_id": chunk.work_id,
                "content": chunk.content,
                "heading_breadcrumbs": chunk.heading_breadcrumbs,
                "enriched_content": chunk.enriched_content,
                "start_line": chunk.start_line,
                "end_line": chunk.end_line,
                "level": chunk.level,
                "rrf_score": chunk.rrf_score,
                "rerank_score": chunk.rerank_score,
                "entity_boost": chunk.entity_boost,
                "final_score": chunk.final_score
            })

        query.retrieved_context = context_data
        session.commit()

        if verbose:
            print(f"  Saved {len(context_data)} results to query.retrieved_context")

        # Save log
        if load_config().logging.enabled:
            _save_retrieval_log(query_id, log_data)

        return RetrievalResult(
            query_id=query_id,
            total_dense_candidates=total_dense,
            total_lexical_candidates=total_lexical,
            rrf_candidates=len(rrf_scores),
            final_count=len(final_chunks),
            chunks=final_chunks
        )
