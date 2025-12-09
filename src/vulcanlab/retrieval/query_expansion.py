"""
Query expansion using Multi-Query Expansion (MQE) and HyDE.

This module expands user queries for better RAG retrieval by generating
alternative queries, hypothetical document answers, and extracting intent/entities.

Uses lazy imports to avoid loading heavy AI dependencies until actually needed.

Usage:
    from vulcanlab.retrieval.query_expansion import expand_query
    result = expand_query("What is working memory?", n=3)

    # Or use individual functions for manual workflow:
    from vulcanlab.retrieval.query_expansion import (
        generate_expansion_prompt,
        parse_expansion_response,
        save_expansion_to_db
    )
    prompt = generate_expansion_prompt("What is working memory?", n=3)
    # ... manually run prompt in LLM ...
    parsed = parse_expansion_response(llm_response)
    query_id = save_expansion_to_db("What is working memory?", parsed)
"""

from __future__ import annotations

import json
from dataclasses import dataclass

from vulcanlab.data.database import get_session
from vulcanlab.data.models import Query
from vulcanlab.data.template_loader import load_template


@dataclass
class QueryExpansionResult:
    """Result of query expansion operation."""

    query_id: int
    original_query: str
    expanded_queries: list[str]
    hyde_answer: str
    intent: str
    entities: list[str]


@dataclass
class ParsedExpansion:
    """Parsed expansion data from LLM response."""

    expanded_queries: list[str]
    hyde_answer: str
    intent: str
    entities: list[str]


def generate_expansion_prompt(query: str, n: int = 3) -> str:
    """Generate the LLM prompt for query expansion.

    This function creates the prompt text without calling the LLM,
    allowing for manual execution of the prompt.

    The prompt template is loaded from the database if available,
    otherwise falls back to the hardcoded default.

    Args:
        query: The original user query.
        n: Number of alternative queries to generate (default 3).

    Returns:
        The complete prompt string to send to an LLM.
    """
    # Define fallback template builder
    def get_fallback_template():
        return """You are a query expansion assistant for a psychology and cognitive science literature RAG system
(textbooks, articles, lecture notes, and research summaries).

Given a user query, you must:
1. Generate {n} alternative phrasings of the query (Multi-Query Expansion).
2. Write a hypothetical answer paragraph that would appear in a psychology textbook (HyDE).
3. Determine the query intent (one label only).
4. Extract key entities (names, theories, key constructs).

CRITICAL FORMAT REQUIREMENTS:
- Respond ONLY with a single valid JSON object.
- No extra text before or after the JSON.
- Use double quotes for all keys and string values.
- Do NOT include comments.
- Do NOT include trailing commas.

User query:
{query}

Your JSON MUST have exactly this structure and keys:

{{
  "queries": ["alternative query 1", "alternative query 2", ...],
  "hyde_answer": "A detailed hypothetical answer paragraph (2-4 sentences) that would appear in a psychology textbook answering this query...",
  "intent": "DEFINITION | MECHANISM | COMPARISON | APPLICATION | STUDY_DETAIL | CRITIQUE",
  "entities": ["entity1", "entity2", ...]
}}

DETAILED INSTRUCTIONS:

1) "queries" (Multi-Query Expansion):
- Generate EXACTLY {n} alternative queries.
- Each query should be 5–15 words.
- Write them as search queries, not full questions (avoid question marks).
- Avoid vague pronouns like "this", "it", "they" that depend on context.
- Make the queries distinct, covering different angles, such as:
  - synonyms and paraphrases,
  - specific theory names or constructs,
  - key researchers or paradigm names,
  - outcomes, mechanisms, or populations involved.
- Focus on psychologically meaningful terms that are likely to appear in headings, abstracts, or key sentences.
- Do NOT answer the question here; these are for retrieval only.

2) "hyde_answer" (Hypothetical Document Embedding – HyDE):
- Write a single paragraph, 2–4 sentences long.
- Tone: neutral, academic, and suitable for a psychology textbook.
- Provide a plausible, high-level answer to the query using established psychological concepts.
- Clearly define key terms and, when appropriate, mention well-known theories or researchers.
- Do NOT refer to "this question", "the user", or the retrieval system.
- Do NOT include citations or references; plain prose only.

3) "intent":
- Choose EXACTLY ONE of the following labels:
  - "DEFINITION"   : The user is asking what something is.
  - "MECHANISM"    : The user is asking how or why something works.
  - "COMPARISON"   : The user is comparing two or more things.
  - "APPLICATION"  : The user is asking for examples or real-world use.
  - "STUDY_DETAIL" : The user is asking about specific study details, results, or methodology.
  - "CRITIQUE"     : The user is asking about limitations, criticisms, or weaknesses.
- If multiple could apply, pick the SINGLE best-fitting label.

4) "entities":
- Return a list of 1–10 key entities.
- Entities can include:
  - researcher names (e.g., "Baumeister", "Spearman"),
  - theory/model names (e.g., "Process Overlap Theory", "CHC model"),
  - core constructs (e.g., "negativity bias", "working memory capacity"),
  - named tasks/paradigms (e.g., "Stroop task", "marshmallow test").
- Avoid generic words like "people", "study", "research" unless they are part of a standard term.
- Prefer concise noun phrases or proper names.
- Do not duplicate entities in the list.

Remember:
- Output MUST be valid JSON matching the schema above.
- Do not include any explanation or commentary outside the JSON."""

    # Load template from database with fallback
    template = load_template("query_expansion", get_fallback_template)

    # Format template with variables
    return template.format(query=query, n=n)


def parse_expansion_response(response_text: str) -> ParsedExpansion:
    """Parse the LLM response into structured expansion data.

    Args:
        response_text: The raw LLM response text (may contain markdown code blocks).

    Returns:
        ParsedExpansion with extracted queries, hyde_answer, intent, and entities.

    Raises:
        ValueError: If response cannot be parsed as valid JSON.
    """
    text = response_text

    # Handle markdown code blocks
    if "```json" in text:
        json_start = text.find("```json") + 7
        json_end = text.find("```", json_start)
        text = text[json_start:json_end].strip()
    elif "```" in text:
        json_start = text.find("```") + 3
        json_end = text.find("```", json_start)
        text = text[json_start:json_end].strip()

    try:
        data = json.loads(text)
    except json.JSONDecodeError as e:
        raise ValueError(f"Failed to parse LLM response as JSON: {e}\nResponse: {response_text}")

    return ParsedExpansion(
        expanded_queries=data.get("queries", []),
        hyde_answer=data.get("hyde_answer", ""),
        intent=data.get("intent", ""),
        entities=data.get("entities", [])
    )


def save_expansion_to_db(query: str, parsed: ParsedExpansion) -> int:
    """Save parsed expansion data to the database.

    Args:
        query: The original user query.
        parsed: ParsedExpansion data from parse_expansion_response.

    Returns:
        The ID of the newly created Query record.
    """
    with get_session() as session:
        query_record = Query(
            original_query=query,
            expanded_queries=parsed.expanded_queries,
            hyde_answer=parsed.hyde_answer,
            intent=parsed.intent,
            entities=parsed.entities,
            vector_status="to_vec"
        )
        session.add(query_record)
        session.commit()
        return query_record.id


def expand_query(
    query: str,
    n: int = 3,
    verbose: bool = False
) -> QueryExpansionResult:
    """Expand a query using MQE and HyDE with intent/entity extraction.

    This is the full pipeline function that generates the prompt, calls the LLM,
    parses the response, and saves to the database.

    Args:
        query: The original user query.
        n: Number of alternative queries to generate (default 3).
        verbose: Whether to print progress information.

    Returns:
        QueryExpansionResult with expanded queries, HyDE answer, intent, entities.

    Raises:
        ValueError: If LLM response cannot be parsed as JSON.
    """
    if verbose:
        print(f"Expanding query: {query}")
        print(f"Generating {n} alternative queries...")

    # Lazy import - only load AI module when LLM is needed
    from vulcanlab.ai.config import ModelTier
    from vulcanlab.ai.llm_factory import create_langchain_chat

    # Generate the prompt
    prompt = generate_expansion_prompt(query, n)

    # Create LangChain chat with FULL model
    langchain_stack = create_langchain_chat(tier=ModelTier.FULL)
    chat = langchain_stack.chat

    # Call the LLM
    if verbose:
        print("Calling LLM...")

    response = chat.invoke(prompt)
    response_text = response.content

    # Parse the response
    parsed = parse_expansion_response(response_text)

    if verbose:
        print(f"Generated {len(parsed.expanded_queries)} alternative queries")
        print(f"Intent: {parsed.intent}")
        print(f"Entities: {len(parsed.entities)}")

    # Save to database
    query_id = save_expansion_to_db(query, parsed)

    if verbose:
        print(f"Saved to database with ID: {query_id}")

    return QueryExpansionResult(
        query_id=query_id,
        original_query=query,
        expanded_queries=parsed.expanded_queries,
        hyde_answer=parsed.hyde_answer,
        intent=parsed.intent,
        entities=parsed.entities
    )
