"""
Vectorize query embeddings for retrieval.

This module creates vector embeddings for Query objects in the database
that are marked for vectorization (vector_status='to_vec').

Uses lazy imports to avoid loading heavy AI dependencies until actually needed.

Usage:
    from vulcanlab.retrieval.query_embeddings import vectorize_query, vectorize_all_queries
    result = vectorize_query(query_id=1, verbose=True)
    result = vectorize_all_queries(verbose=True)
"""

from __future__ import annotations

from dataclasses import dataclass

from vulcanlab.data.database import get_session
from vulcanlab.data.models import Query


@dataclass
class QueryVectorizationResult:
    """Result of query vectorization operation."""

    query_id: int
    total_embeddings: int
    original_count: int
    mqe_count: int
    hyde_count: int
    success: bool
    error: str | None = None


@dataclass
class BatchVectorizationResult:
    """Result of batch query vectorization operation."""

    total_queries: int
    processed: int
    success: int
    failed: int
    total_embeddings: int
    errors: list[tuple[int, str]]  # (query_id, error_message)


def get_pending_queries_count() -> int:
    """Get count of queries eligible for vectorization.

    Returns:
        Number of queries with vector_status='to_vec'.
    """
    with get_session() as session:
        return session.query(Query).filter(
            Query.vector_status == 'to_vec'
        ).count()


def vectorize_query(
    query_id: int,
    verbose: bool = False
) -> QueryVectorizationResult:
    """Vectorize a single query using embedding model.

    Args:
        query_id: ID of the query in the database.
        verbose: Whether to print progress information.

    Returns:
        QueryVectorizationResult with counts and status.

    Raises:
        ValueError: If query not found.
    """
    with get_session() as session:
        # Fetch the query
        query = session.query(Query).filter(Query.id == query_id).first()
        if not query:
            raise ValueError(f"Query with ID {query_id} not found")

        if verbose:
            print(f"Vectorizing query {query_id}: {query.original_query[:50]}...")

        # Build list of texts to embed
        texts_to_embed = []

        # Original query
        texts_to_embed.append(query.original_query)
        original_count = 1

        # MQE queries
        mqe_queries = query.expanded_queries or []
        texts_to_embed.extend(mqe_queries)
        mqe_count = len(mqe_queries)

        # HyDE answer
        hyde_count = 0
        if query.hyde_answer:
            texts_to_embed.append(query.hyde_answer)
            hyde_count = 1

        total_embeddings = len(texts_to_embed)

        if verbose:
            print(f"  Generating {total_embeddings} embeddings: {original_count} original, {mqe_count} MQE, {hyde_count} HyDE")

        try:
            # Lazy import - only load AI module when embeddings are needed
            from vulcanlab.ai.llm_factory import create_embeddings

            # Create embeddings model and generate embeddings in one batch
            embeddings_model = create_embeddings()
            embeddings = embeddings_model.embed_documents(texts_to_embed)

            # Assign embeddings to query fields
            idx = 0

            # Original embedding
            query.embedding_original = embeddings[idx]
            idx += 1

            # MQE embeddings (as JSON array)
            if mqe_count > 0:
                query.embeddings_mqe = embeddings[idx:idx + mqe_count]
                idx += mqe_count

            # HyDE embedding
            if hyde_count > 0:
                query.embedding_hyde = embeddings[idx]

            # Update status
            query.vector_status = 'vec'
            session.commit()

            if verbose:
                print(f"  Successfully vectorized query {query_id}")

            return QueryVectorizationResult(
                query_id=query_id,
                total_embeddings=total_embeddings,
                original_count=original_count,
                mqe_count=mqe_count,
                hyde_count=hyde_count,
                success=True
            )

        except Exception as e:
            # Mark as error
            query.vector_status = 'vec_err'
            session.commit()

            if verbose:
                print(f"  Error vectorizing query {query_id}: {e}")

            return QueryVectorizationResult(
                query_id=query_id,
                total_embeddings=0,
                original_count=0,
                mqe_count=0,
                hyde_count=0,
                success=False,
                error=str(e)
            )


def vectorize_all_queries(
    verbose: bool = False
) -> BatchVectorizationResult:
    """Vectorize all queries with vector_status='to_vec'.

    Args:
        verbose: Whether to print progress information.

    Returns:
        BatchVectorizationResult with aggregate counts and errors.
    """
    with get_session() as session:
        # Get all pending queries
        queries = session.query(Query).filter(
            Query.vector_status == 'to_vec'
        ).all()

        total_queries = len(queries)

        if verbose:
            print(f"Found {total_queries} queries to vectorize")

        if not queries:
            return BatchVectorizationResult(
                total_queries=0,
                processed=0,
                success=0,
                failed=0,
                total_embeddings=0,
                errors=[]
            )

        success_count = 0
        failed_count = 0
        total_embeddings = 0
        errors = []

        for i, query in enumerate(queries):
            if verbose:
                print(f"\nProcessing query {i + 1}/{total_queries} (ID: {query.id})")

            result = vectorize_query(query.id, verbose=verbose)

            if result.success:
                success_count += 1
                total_embeddings += result.total_embeddings
            else:
                failed_count += 1
                errors.append((query.id, result.error or "Unknown error"))

        if verbose:
            print(f"\nCompleted: {success_count} success, {failed_count} failed")
            print(f"Total embeddings generated: {total_embeddings}")

        return BatchVectorizationResult(
            total_queries=total_queries,
            processed=total_queries,
            success=success_count,
            failed=failed_count,
            total_embeddings=total_embeddings,
            errors=errors
        )
