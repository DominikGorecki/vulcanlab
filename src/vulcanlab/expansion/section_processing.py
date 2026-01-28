"""
Section processing module for RAG expansion pipeline.

This module handles:
- Running the full RAG pipeline for individual expansion sections
- Generating section responses via LLM
- Saving manual responses for manual mode

Usage:
    from vulcanlab.expansion.section_processing import (
        expand_section, generate_section, save_manual_response
    )

    # Run RAG pipeline for a section
    expand_section(section_id, session)

    # Generate response via LLM (automatic mode)
    generate_section(section_id, session, llm_client)

    # Save manual response (manual mode)
    save_manual_response(section_id, response_text, session)
"""

from __future__ import annotations

import logging
from typing import Protocol, Any

from sqlalchemy.orm import Session

from vulcanlab.data.models.expansion import (
    ExpansionSection,
    SectionStatus,
)
from vulcanlab.retrieval.query_expansion import (
    generate_expansion_prompt as generate_query_expansion_prompt,
    parse_expansion_response,
    ParsedExpansion,
    ExpansionResponseSchema,
)
from vulcanlab.data.template_loader import get_active_template


logger = logging.getLogger(__name__)


class LLMClient(Protocol):
    """Protocol for LLM client interface."""

    def invoke(self, prompt: str) -> Any:
        """Invoke the LLM with a prompt and return the response."""
        ...

    def with_structured_output(self, schema: type) -> "LLMClient":
        """Return a client configured for structured output."""
        ...


def _expand_query_for_section(
    expansion_prompt: str,
    llm_client: LLMClient,
    n: int = 3
) -> ParsedExpansion:
    """Run query expansion on the section's expansion prompt.

    Uses the existing query expansion logic to generate:
    - Alternative query phrasings (MQE)
    - Hypothetical answer (HyDE)
    - Intent classification
    - Entity extraction

    Args:
        expansion_prompt: The section's expansion prompt.
        llm_client: LLM client for expansion.
        n: Number of alternative queries to generate.

    Returns:
        ParsedExpansion with expanded queries, HyDE, intent, entities.
    """
    # Generate the expansion prompt
    prompt = generate_query_expansion_prompt(expansion_prompt, n)

    # Call LLM with structured output
    try:
        structured_client = llm_client.with_structured_output(ExpansionResponseSchema)
        response = structured_client.invoke(prompt)

        # Convert Pydantic model to ParsedExpansion
        return ParsedExpansion(
            expanded_queries=response.queries,
            hyde_answer=response.hyde_answer,
            intent=response.intent,
            entities=response.entities
        )
    except AttributeError:
        # Fallback to raw invocation
        logger.warning("Structured output not supported, using raw invocation")
        response = llm_client.invoke(prompt)
        return parse_expansion_response(str(response))


def _generate_embeddings_for_section(
    original_query: str,
    expanded_queries: list[str],
    hyde_answer: str | None
) -> dict:
    """Generate embeddings for section queries.

    Args:
        original_query: The section's expansion prompt.
        expanded_queries: Alternative query phrasings from MQE.
        hyde_answer: Hypothetical answer from HyDE.

    Returns:
        Dict with embedding_original, embeddings_mqe, embedding_hyde.
    """
    from vulcanlab.ai.llm_factory import create_embeddings

    texts_to_embed = [original_query]
    texts_to_embed.extend(expanded_queries)
    if hyde_answer:
        texts_to_embed.append(hyde_answer)

    embeddings_model = create_embeddings()
    embeddings = embeddings_model.embed_documents(texts_to_embed)

    idx = 0
    result = {
        "embedding_original": embeddings[idx]
    }
    idx += 1

    if expanded_queries:
        result["embeddings_mqe"] = embeddings[idx:idx + len(expanded_queries)]
        idx += len(expanded_queries)

    if hyde_answer:
        result["embedding_hyde"] = embeddings[idx]

    return result


def _retrieve_for_section(
    session: Session,
    embedding_original: list[float],
    embeddings_mqe: list[list[float]] | None,
    embedding_hyde: list[float] | None,
    entities: list[str] | None,
    intent: str | None,
    original_query: str,
    expanded_queries: list[str] | None
) -> list[dict]:
    """Run retrieval pipeline for section embeddings.

    Uses the existing retrieval infrastructure but operates on in-memory
    embeddings rather than Query objects in the database.

    Args:
        session: Database session.
        embedding_original: Original query embedding.
        embeddings_mqe: MQE query embeddings.
        embedding_hyde: HyDE answer embedding.
        entities: Extracted entities for bias.
        intent: Query intent for bias.
        original_query: Original query text for lexical search.
        expanded_queries: Expanded query texts for lexical search.

    Returns:
        List of retrieved context dicts (similar to query.retrieved_context).
    """
    # Import here to avoid circular imports
    from vulcanlab.retrieval.retrieve import (
        _dense_search,
        _lexical_search,
        _compute_rrf_scores,
        _rerank_chunks,
        _apply_entity_bias,
        _apply_intent_bias,
        _apply_mmr_diversity,
        enrich_chunk_from_parent,
        RetrievedChunk,
        DEFAULT_DENSE_LIMIT,
        DEFAULT_LEXICAL_LIMIT,
        DEFAULT_RRF_K,
        DEFAULT_TOP_K_RRF,
        DEFAULT_TOP_N_FINAL,
        DEFAULT_ENTITY_BOOST,
        DEFAULT_MIN_WORD_COUNT,
        DEFAULT_MAX_WORD_COUNT,
        DEFAULT_MMR_LAMBDA,
    )
    from vulcanlab.data.models import Chunk, Work
    import numpy as np

    # Collect all embeddings for dense search
    embeddings = [embedding_original]
    if embeddings_mqe is not None:
        embeddings.extend(embeddings_mqe)
    if embedding_hyde is not None:
        embeddings.append(embedding_hyde)

    # Collect query texts for lexical search
    query_texts = [original_query]
    if expanded_queries:
        query_texts.extend(expanded_queries)

    # Dense retrieval
    dense_results = []
    for emb in embeddings:
        results = _dense_search(session, emb, DEFAULT_DENSE_LIMIT)
        dense_results.append(results)

    # Lexical retrieval
    lexical_results = []
    for text in query_texts:
        results = _lexical_search(session, text, DEFAULT_LEXICAL_LIMIT)
        lexical_results.append(results)

    # RRF fusion
    all_results = dense_results + lexical_results
    rrf_scores = _compute_rrf_scores(all_results, DEFAULT_RRF_K)

    # Sort by RRF score and take top_k_rrf
    sorted_ids = sorted(rrf_scores.keys(), key=lambda x: rrf_scores[x], reverse=True)
    top_ids = sorted_ids[:DEFAULT_TOP_K_RRF]

    if not top_ids:
        return []

    # Fetch chunk data
    chunks_data = session.query(Chunk).filter(Chunk.id.in_(top_ids)).all()
    chunks_map = {c.id: c for c in chunks_data}
    embeddings_map = {c.id: c.embedding for c in chunks_data}

    # Get work data
    work_ids = {c.work_id for c in chunks_data}
    works = session.query(Work).filter(Work.id.in_(work_ids)).all()
    works_map = {w.id: w for w in works}

    # Build RetrievedChunk objects
    retrieved_chunks = []
    for chunk_id in top_ids:
        if chunk_id not in chunks_map:
            continue

        chunk = chunks_map[chunk_id]
        work = works_map.get(chunk.work_id)

        # Enrich content
        try:
            enrich_result = enrich_chunk_from_parent(
                chunk, session,
                min_word_count=DEFAULT_MIN_WORD_COUNT,
                max_word_count=DEFAULT_MAX_WORD_COUNT
            )
            enriched = enrich_result['content']
            parent_id = enrich_result['parent_id']
            start_line = enrich_result.get('start_line', chunk.start_line)
            end_line = enrich_result.get('end_line', chunk.end_line)
        except Exception as e:
            logger.warning(f"Enrichment failed for chunk {chunk.id}: {e}")
            enriched = chunk.content
            parent_id = chunk.parent_id
            start_line = chunk.start_line
            end_line = chunk.end_line

        # Get embedding for MMR
        embedding = embeddings_map.get(chunk_id)
        np_embedding = np.array(embedding, dtype=np.float32) if embedding is not None else None

        retrieved_chunks.append(RetrievedChunk(
            id=chunk.id,
            parent_id=parent_id if enrich_result.get('enriched') else chunk.parent_id,
            work_id=chunk.work_id,
            work_title=work.title if work else None,
            work_authors=work.authors if work else None,
            work_year=work.year if work else None,
            content=chunk.content,
            enriched_content=enriched,
            start_line=start_line,
            end_line=end_line,
            level=chunk.level,
            heading_breadcrumbs=chunk.heading_breadcrumbs,
            rrf_score=rrf_scores[chunk_id],
            _embedding=np_embedding
        ))

    if not retrieved_chunks:
        return []

    # Rerank
    retrieved_chunks = _rerank_chunks(original_query, retrieved_chunks)

    # Apply biases
    retrieved_chunks = _apply_entity_bias(retrieved_chunks, entities or [], DEFAULT_ENTITY_BOOST)
    retrieved_chunks = _apply_intent_bias(retrieved_chunks, intent)

    # Sort by final_score
    retrieved_chunks.sort(key=lambda x: x.final_score, reverse=True)

    # Apply MMR diversity
    final_chunks = _apply_mmr_diversity(retrieved_chunks, DEFAULT_TOP_N_FINAL, DEFAULT_MMR_LAMBDA)

    # Convert to context dicts
    context_data = []
    for chunk in final_chunks:
        context_data.append({
            "id": chunk.id,
            "parent_id": chunk.parent_id,
            "work_id": chunk.work_id,
            "work_title": chunk.work_title,
            "work_authors": chunk.work_authors,
            "work_year": chunk.work_year,
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

    return context_data


def _consolidate_section_context(
    session: Session,
    retrieved_context: list[dict]
) -> list[dict]:
    """Consolidate retrieved context for a section.

    Uses similar logic to consolidate_context but operates on in-memory
    context rather than Query objects.

    Args:
        session: Database session.
        retrieved_context: List of retrieved context dicts.

    Returns:
        List of consolidated context dicts.
    """
    from vulcanlab.augmentation.consolidate_context import (
        _calculate_coverage,
        _merge_adjacent_items,
        _get_heading_chain,
        DEFAULT_COVERAGE_THRESHOLD,
        DEFAULT_LINE_GAP,
        DEFAULT_ENRICH_FROM_PARENT,
    )
    from vulcanlab.data.models import Chunk, Work
    from collections import defaultdict

    if not retrieved_context:
        return []

    # Get all work IDs and parent IDs
    work_ids = {item['work_id'] for item in retrieved_context}
    works = session.query(Work).filter(Work.id.in_(work_ids)).all()
    works_map = {w.id: w for w in works}

    parent_ids = {item['parent_id'] for item in retrieved_context if item.get('parent_id')}

    # Build parent hierarchy
    all_parent_ids = set(parent_ids)
    parents_to_check = list(parent_ids)
    while parents_to_check:
        next_level = session.query(Chunk).filter(Chunk.id.in_(parents_to_check)).all()
        parents_to_check = []
        for p in next_level:
            if p.parent_id and p.parent_id not in all_parent_ids:
                all_parent_ids.add(p.parent_id)
                parents_to_check.append(p.parent_id)

    all_parents = session.query(Chunk).filter(Chunk.id.in_(all_parent_ids)).all()
    parents_map = {p.id: p for p in all_parents}

    # Convert to working items
    items = []
    for ctx in retrieved_context:
        items.append({
            'id': ctx.get('id'),
            'chunk_ids': [ctx['id']],
            'parent_id': ctx.get('parent_id'),
            'work_id': ctx.get('work_id'),
            'content': ctx.get('enriched_content') or ctx.get('content', ''),
            'start_line': ctx['start_line'],
            'end_line': ctx['end_line'],
            'score': ctx.get('final_score', 0),
            'level': ctx.get('level'),
            'heading_breadcrumbs': ctx.get('heading_breadcrumbs')
        })

    # Iterative consolidation
    processed = True
    while processed:
        processed = False

        groups = defaultdict(list)
        for item in items:
            key = (item['work_id'], item.get('parent_id'))
            groups[key].append(item)

        new_items = []

        for (work_id, parent_id), group_items in groups.items():
            parent = parents_map.get(parent_id) if parent_id else None

            if parent and parent.content:
                coverage = _calculate_coverage(group_items, parent)

                if coverage >= DEFAULT_COVERAGE_THRESHOLD:
                    # Replace with parent
                    score = max(item['score'] for item in group_items)
                    chunk_ids = []
                    for item in group_items:
                        chunk_ids.extend(item.get('chunk_ids', [item.get('id')]))

                    new_items.append({
                        'chunk_ids': chunk_ids,
                        'parent_id': parent.parent_id,
                        'work_id': work_id,
                        'content': parent.content,
                        'start_line': parent.start_line,
                        'end_line': parent.end_line,
                        'score': score,
                        'level': parent.level
                    })
                    processed = True
                else:
                    merged = _merge_adjacent_items(
                        group_items, parent, DEFAULT_LINE_GAP, DEFAULT_ENRICH_FROM_PARENT
                    )
                    if len(merged) < len(group_items):
                        processed = True
                    new_items.extend(merged)
            else:
                merged = _merge_adjacent_items(
                    group_items, None, DEFAULT_LINE_GAP, DEFAULT_ENRICH_FROM_PARENT
                )
                if len(merged) < len(group_items):
                    processed = True
                new_items.extend(merged)

        items = new_items

    # Build final result
    result = []
    for item in items:
        heading_chain = _get_heading_chain(item.get('parent_id'), parents_map)
        work = works_map.get(item['work_id'])

        result.append({
            'id': item.get('chunk_ids', [None])[0],
            'chunk_ids': item.get('chunk_ids', []),
            'parent_id': item.get('parent_id'),
            'work_id': item['work_id'],
            'content': item['content'],
            'start_line': item['start_line'],
            'end_line': item['end_line'],
            'score': item['score'],
            'heading_chain': heading_chain,
            'work_title': work.title if work else None,
            'work_authors': work.authors if work else None,
            'work_year': work.year if work else None
        })

    # Sort by score
    result.sort(key=lambda x: x['score'], reverse=True)
    return result


def expand_section(
    section_id: int,
    session: Session,
    llm_client: LLMClient | None = None
) -> None:
    """Run the full RAG pipeline for an expansion section.

    This function:
    1. Loads the section from the database
    2. Runs query expansion (MQE, HyDE, intent, entities)
    3. Generates embeddings for the expanded queries
    4. Retrieves relevant chunks
    5. Consolidates the context
    6. Stores results in the section record

    If llm_client is not provided, uses the default LLM configuration.

    Args:
        section_id: ID of the ExpansionSection to expand.
        session: Database session.
        llm_client: Optional LLM client for query expansion.

    Raises:
        ValueError: If section not found.
    """
    # Load section
    section = session.query(ExpansionSection).filter(
        ExpansionSection.id == section_id
    ).first()
    if not section:
        raise ValueError(f"ExpansionSection with ID {section_id} not found")

    logger.info(f"Starting expansion for section {section_id}: {section.heading}")

    # Update status
    section.status = SectionStatus.EXPANDING
    session.commit()

    try:
        # Get LLM client if not provided
        if llm_client is None:
            from vulcanlab.ai.config import ModelTier
            from vulcanlab.ai.llm_factory import create_langchain_chat

            langchain_stack = create_langchain_chat(tier=ModelTier.FULL)
            llm_client = langchain_stack.chat

        # Run query expansion
        parsed = _expand_query_for_section(section.expansion_prompt, llm_client)

        # Store expansion results
        section.expanded_queries = {"queries": parsed.expanded_queries}
        section.hyde_answer = parsed.hyde_answer
        section.intent = parsed.intent
        section.entities = {"entities": parsed.entities}

        # Generate embeddings
        embeddings_data = _generate_embeddings_for_section(
            section.expansion_prompt,
            parsed.expanded_queries,
            parsed.hyde_answer
        )

        # Retrieve chunks
        retrieved_context = _retrieve_for_section(
            session,
            embeddings_data["embedding_original"],
            embeddings_data.get("embeddings_mqe"),
            embeddings_data.get("embedding_hyde"),
            parsed.entities,
            parsed.intent,
            section.expansion_prompt,
            parsed.expanded_queries
        )

        # Store retrieved context
        section.retrieved_context = {"chunks": retrieved_context}

        # Consolidate context
        clean_context = _consolidate_section_context(session, retrieved_context)
        section.clean_retrieval_context = {"chunks": clean_context}

        # Update status to ready
        section.status = SectionStatus.READY
        session.commit()

        logger.info(
            f"Expansion complete for section {section_id}: "
            f"{len(retrieved_context)} chunks retrieved, "
            f"{len(clean_context)} after consolidation"
        )

    except Exception as e:
        logger.error(f"Expansion failed for section {section_id}: {e}")
        section.status = SectionStatus.FAILED
        section.error_message = str(e)
        session.commit()
        raise


def _format_section_context(clean_context: list[dict]) -> str:
    """Format consolidated context for augmented prompt.

    Args:
        clean_context: List of consolidated context dicts.

    Returns:
        Formatted context string.
    """
    if not clean_context:
        return "(No context available)"

    blocks = []
    for idx, ctx in enumerate(clean_context, start=1):
        work_title = ctx.get('work_title', 'Unknown')
        heading_chain = ctx.get('heading_chain', [])
        content = ctx.get('content', '')
        work_id = ctx.get('work_id')
        start_line = ctx.get('start_line', 0)
        end_line = ctx.get('end_line', 0)

        if heading_chain:
            breadcrumb_path = " > ".join(heading_chain)
            source_path = f"{work_title} > {breadcrumb_path}"
        else:
            source_path = work_title

        block = f"""[S{idx}] Source: {source_path} | (work_id={work_id}, start-line={start_line}, end-line={end_line})
Text:
{content.strip()}"""
        blocks.append(block)

    return "\n\n".join(blocks)


def generate_section(
    section_id: int,
    session: Session,
    llm_client: LLMClient
) -> None:
    """Generate the LLM response for an expansion section.

    This function:
    1. Loads the section from the database
    2. Builds the augmented prompt from retrieved context
    3. Calls the LLM to generate the response
    4. Stores the response in the section record

    Args:
        section_id: ID of the ExpansionSection to generate.
        session: Database session.
        llm_client: LLM client for response generation.

    Raises:
        ValueError: If section not found or not ready for generation.
    """
    # Load section
    section = session.query(ExpansionSection).filter(
        ExpansionSection.id == section_id
    ).first()
    if not section:
        raise ValueError(f"ExpansionSection with ID {section_id} not found")

    if section.status not in [SectionStatus.READY, SectionStatus.FAILED]:
        raise ValueError(
            f"Section {section_id} is not ready for generation "
            f"(status: {section.status.value})"
        )

    logger.info(f"Starting generation for section {section_id}: {section.heading}")

    # Update status
    section.status = SectionStatus.GENERATING
    session.commit()

    try:
        # Get clean context
        clean_context = section.clean_retrieval_context.get("chunks", []) if section.clean_retrieval_context else []

        # Format context
        context_blocks = _format_section_context(clean_context)

        # Build augmented prompt using expansion_section_generation template
        template_content = get_active_template("expansion_section_generation", session)

        # Extract entities from stored data
        entities_data = section.entities or {}
        entities_list = entities_data.get("entities", [])
        entities_str = ", ".join(str(e) for e in entities_list) if entities_list else "None specified"

        augmented_prompt = template_content.format(
            section_heading=section.heading,
            section_summary=section.summary or "",
            intent=section.intent or "GENERAL",
            entities_str=entities_str,
            context_blocks=context_blocks,
            user_question=section.expansion_prompt
        )

        # Store augmented prompt
        section.augmented_prompt = augmented_prompt

        # Call LLM
        response = llm_client.invoke(augmented_prompt)

        # Extract response text
        if hasattr(response, 'content'):
            response_text = response.content
        else:
            response_text = str(response)

        # Store response
        section.response_text = response_text
        section.status = SectionStatus.COMPLETED
        session.commit()

        logger.info(f"Generation complete for section {section_id}")

    except Exception as e:
        logger.error(f"Generation failed for section {section_id}: {e}")
        section.status = SectionStatus.FAILED
        section.error_message = str(e)
        session.commit()
        raise


def save_manual_response(
    section_id: int,
    response_text: str,
    session: Session
) -> None:
    """Save a user-provided manual response for a section.

    This function is used in manual mode where the user copies the
    augmented prompt, runs it externally, and pastes the response.

    Args:
        section_id: ID of the ExpansionSection.
        response_text: The manual response text to save.
        session: Database session.

    Raises:
        ValueError: If section not found.
    """
    # Load section
    section = session.query(ExpansionSection).filter(
        ExpansionSection.id == section_id
    ).first()
    if not section:
        raise ValueError(f"ExpansionSection with ID {section_id} not found")

    logger.info(f"Saving manual response for section {section_id}: {section.heading}")

    # Store response
    section.response_text = response_text
    section.status = SectionStatus.COMPLETED
    session.commit()

    logger.info(f"Manual response saved for section {section_id}")
