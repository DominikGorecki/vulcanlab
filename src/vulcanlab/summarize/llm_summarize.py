"""
LLM Summarization Module for generating structured summaries from evidence packets.
"""

import json
import logging
import time
import random
from dataclasses import dataclass, field
from typing import List, Optional, Dict, Any
from functools import wraps
from sqlalchemy.orm import Session
from sqlalchemy import select

from vulcanlab.data.models.prompt_template import PromptTemplate
from vulcanlab.summarize.evidence import EvidencePacket, Snippet
from vulcanlab.config.app_config import load_config
from vulcanlab.ai.llm_factory import create_langchain_chat
from vulcanlab.ai.config import ModelTier
from vulcanlab.summarize.exceptions import (
    LLMAPIError,
    LLMRateLimitError,
    LLMTimeoutError,
    LLMResponseError,
    InsufficientEvidenceError,
    SummarizationError
)

logger = logging.getLogger(__name__)

@dataclass
class KeyPoint:
    text: str
    start_line: int
    end_line: int

@dataclass
class Definition:
    term: str
    definition: str
    start_line: int
    end_line: int

@dataclass
class KeyTerm:
    term: str
    start_line: int
    end_line: int

@dataclass
class Example:
    text: str
    start_line: int
    end_line: int

@dataclass
class TokenUsage:
    input_tokens: int
    output_tokens: int
    model: str

@dataclass
class SummaryResponse:
    gist: str
    key_points: List[KeyPoint] = field(default_factory=list)
    definitions: List[Definition] = field(default_factory=list)
    key_terms: List[KeyTerm] = field(default_factory=list)
    examples: List[Example] = field(default_factory=list)
    insufficient_evidence: bool = False
    missing_concepts: List[str] = field(default_factory=list)
    token_usage: Optional[TokenUsage] = None


def get_active_template(function_tag: str, session: Session) -> str:
    """
    Queries the prompt_templates table for the active template by function_tag.
    """
    stmt = (
        select(PromptTemplate)
        .where(
            PromptTemplate.function_tag == function_tag,
            PromptTemplate.is_active == True
        )
        .order_by(PromptTemplate.version.desc())
    )
    result = session.execute(stmt)
    template = result.scalar_one_or_none()
    
    if not template:
        raise ValueError(f"No active prompt template found for function_tag: {function_tag}")
        
    return template.template_content


def build_summarization_prompt(evidence: EvidencePacket, session: Session, chunk_id: Optional[str] = None) -> str:
    """
    Builds the summarization prompt using the active template and evidence packet.
    """
    logger.debug(f"Building prompt for node {chunk_id or evidence.heading_path}, evidence snippets: {len(evidence.snippets)}")
    template_content = get_active_template("summarize_node", session)
    
    # Format snippets
    snippets_text = ""
    for i, s in enumerate(evidence.snippets):
        snippets_text += f"Snippet {i+1} (Lines {s.start_line}-{s.end_line}): {s.text}\n"
    
    # Format stats
    stats_text = json.dumps(evidence.stats, indent=2)
    
    # Format keyphrases
    keyphrases_text = ", ".join(evidence.keyphrases)
    
    # Final formatting
    prompt = template_content.format(
        heading_path=evidence.heading_path,
        line_start=evidence.line_start,
        line_end=evidence.line_end,
        line_range=f"{evidence.line_start}-{evidence.line_end}",
        snippets=snippets_text,
        keyphrases=keyphrases_text,
        stats=stats_text
    )
    
    return prompt


def llm_retry(max_retries: int = 3, base_delay: float = 1.0):
    """
    Decorator for retrying LLM calls with exponential backoff and jitter.
    """
    def decorator(func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            last_exception = None
            for attempt in range(max_retries + 1):
                try:
                    return func(*args, **kwargs)
                except (LLMRateLimitError, LLMTimeoutError, LLMResponseError) as e:
                    last_exception = e
                    if attempt == max_retries:
                        break
                    
                    # Determine delay
                    delay = base_delay * (2 ** attempt)
                    if hasattr(e, 'retry_after') and e.retry_after:
                        delay = max(delay, e.retry_after)
                    
                    # Add jitter (up to 20% of delay)
                    jitter = delay * 0.2 * random.random()
                    total_delay = delay + jitter
                    
                    logger.warning(
                        f"Retrying LLM call due to {type(e).__name__} (attempt {attempt + 1}/{max_retries}). "
                        f"Sleeping for {total_delay:.2f}s"
                    )
                    time.sleep(total_delay)
                except LLMAPIError as e:
                    # Non-retryable API errors
                    logger.error(f"Non-retryable LLM API error: {e}")
                    raise
                except Exception as e:
                    # Unexpected errors
                    logger.error(f"Unexpected error in LLM call: {e}")
                    raise
            
            logger.error(f"Max retries reached for LLM call. Last error: {last_exception}")
            raise last_exception
        return wrapper
    return decorator


def get_llm_model() -> str:
    """
    Reads the configured LLM model from vulcanlab.config.
    """
    config = load_config()
    provider = config.llm.provider
    if provider == "openai":
        return config.llm.models.openai.full
    elif provider == "gemini":
        return config.llm.models.gemini.full
    return "gpt-4o" # Fallback


def call_llm(prompt: str, model: str) -> tuple[str, TokenUsage]:
    """
    Calls the LLM. Raises LLMAPIError or its subclasses on failure.
    Returns (response_content, token_usage).
    """
    chat_stack = create_langchain_chat(tier=ModelTier.FULL)
    chat = chat_stack.chat
    
    try:
        start_time = time.time()
        response = chat.invoke(prompt)
        duration = time.time() - start_time
        
        # Extract usage
        usage_data = getattr(response, 'response_metadata', {}).get('token_usage', {})
        token_usage = TokenUsage(
            input_tokens=usage_data.get('prompt_tokens', 0) or usage_data.get('input_tokens', 0),
            output_tokens=usage_data.get('completion_tokens', 0) or usage_data.get('output_tokens', 0),
            model=model
        )
        
        logger.info(f"LLM call completed in {duration:.2f}s, tokens: input={token_usage.input_tokens}, output={token_usage.output_tokens}")

        # Handle both string and list content formats (Gemini returns list of content blocks)
        content = response.content
        if isinstance(content, list):
            # Extract text from content blocks - handle both dict and string items
            text_parts = []
            for block in content:
                if isinstance(block, dict) and block.get('type') == 'text':
                    text_parts.append(block.get('text', ''))
                elif isinstance(block, str):
                    text_parts.append(block)
                elif hasattr(block, 'text'):
                    # Handle object-style content blocks (e.g., Pydantic models)
                    text_parts.append(block.text)
            content = ''.join(text_parts)

        return content, token_usage
        
    except Exception as e:
        msg = str(e).lower()
        status_code = None
        
        # Try to extract status code if available
        if hasattr(e, 'status_code'):
            status_code = e.status_code
        elif '429' in msg:
            status_code = 429
        elif 'timeout' in msg or 'deadline exceeded' in msg:
            raise LLMTimeoutError(f"LLM API timeout: {e}")
        elif '400' in msg:
            status_code = 400
        elif '401' in msg or '403' in msg:
            status_code = 401
        elif any(code in msg for code in ['500', '502', '503']):
            status_code = 500

        if status_code == 429:
            # Check for Retry-After if possible (though difficult with LangChain)
            retry_after = None
            raise LLMRateLimitError(f"LLM Rate limit reached: {e}", status_code=429, retry_after=retry_after)
        elif status_code in [500, 502, 503]:
            raise LLMAPIError(f"LLM Server error ({status_code}): {e}", status_code=status_code)
        elif status_code in [400, 401, 403]:
            raise LLMAPIError(f"LLM Client error ({status_code}): {e}", status_code=status_code)
        
        # Generic error
        raise LLMAPIError(f"LLM API error: {e}")


def parse_llm_response(response_text: str, evidence: EvidencePacket) -> SummaryResponse:
    """
    Parses the LLM response into a SummaryResponse object.
    Validates line numbers against the evidence packet range.
    Raises LLMResponseError on malformed response.
    """
    try:
        # Extract JSON if LLM added markdown fences
        json_str = response_text
        if "```json" in response_text:
            json_str = response_text.split("```json")[1].split("```")[0].strip()
        elif "```" in response_text:
            json_str = response_text.split("```")[1].split("```")[0].strip()
            
        data = json.loads(json_str)
        
        # Check for required fields
        if "gist" not in data:
            raise LLMResponseError("LLM response missing required field: 'gist'")

        def validate_lines(start: int, end: int) -> tuple[int, int]:
            # Clamp lines to evidence range if needed
            s = max(evidence.line_start, min(evidence.line_end, start))
            e = max(evidence.line_start, min(evidence.line_end, end))
            return s, e

        key_points = []
        for kp in data.get("key_points", []):
            s, e = validate_lines(kp.get("start_line", 0), kp.get("end_line", 0))
            key_points.append(KeyPoint(text=kp.get("text", ""), start_line=s, end_line=e))
            
        definitions = []
        for d in data.get("definitions", []):
            s, e = validate_lines(d.get("start_line", 0), d.get("end_line", 0))
            definitions.append(Definition(
                term=d.get("term", ""),
                definition=d.get("definition", ""),
                start_line=s,
                end_line=e
            ))
            
        key_terms = []
        for kt in data.get("key_terms", []):
            # Handle both string format ["term1", "term2"] and object format [{"term": "...", ...}]
            if isinstance(kt, str):
                key_terms.append(KeyTerm(term=kt, start_line=0, end_line=0))
            else:
                s, e = validate_lines(kt.get("start_line", 0), kt.get("end_line", 0))
                key_terms.append(KeyTerm(term=kt.get("term", ""), start_line=s, end_line=e))
            
        examples = []
        for ex in data.get("examples", []):
            s, e = validate_lines(ex.get("start_line", 0), ex.get("end_line", 0))
            examples.append(Example(text=ex.get("text", ""), start_line=s, end_line=e))
            
        return SummaryResponse(
            gist=data.get("gist", ""),
            key_points=key_points,
            definitions=definitions,
            key_terms=key_terms,
            examples=examples,
            insufficient_evidence=data.get("insufficient_evidence", False),
            missing_concepts=data.get("missing_concepts", [])
        )
        
    except (json.JSONDecodeError, KeyError, TypeError) as e:
        logger.error(f"Failed to parse LLM response: {e}. Response: {response_text}")
        raise LLMResponseError(f"Malformed LLM response: {e}")


def handle_escalation(
    evidence: EvidencePacket, 
    missing_concepts: List[str], 
    full_content: str
) -> str:
    """
    Extracts additional sentences related to missing concepts to provide more context.
    """
    if not missing_concepts or not full_content:
        return ""
        
    additional_sentences = []
    lines = full_content.splitlines()
    
    for concept in missing_concepts:
        # Simple search for concept in full content
        # We look outside the current evidence range if possible
        for i, line in enumerate(lines):
            line_num = i + 1
            # Check if this line is OUTSIDE the current evidence range
            if line_num < evidence.line_start or line_num > evidence.line_end:
                if concept.lower() in line.lower():
                    # Take this line and maybe one before/after
                    start = max(0, i - 1)
                    end = min(len(lines), i + 2)
                    context_snippet = "\n".join(lines[start:end])
                    additional_sentences.append(f"Context for '{concept}' (Lines {start+1}-{end}):\n{context_snippet}")
                    break # Just one snippet per concept for now
                    
    return "\n\n".join(additional_sentences)


@llm_retry(max_retries=3)
def _call_and_parse(prompt: str, model: str, evidence: EvidencePacket) -> SummaryResponse:
    """
    Helper to call LLM and parse response with retry logic.
    """
    response_text, token_usage = call_llm(prompt, model)
    summary = parse_llm_response(response_text, evidence)
    summary.token_usage = token_usage
    return summary


def summarize_node(
    evidence: EvidencePacket, 
    session: Session,
    full_content: Optional[str] = None,
    additional_context: Optional[str] = None,
    chunk_id: Optional[str] = None
) -> SummaryResponse:
    """
    Orchestrates the summarization of a single node.
    Includes escalation logic if evidence is insufficient.
    """
    prompt = build_summarization_prompt(evidence, session, chunk_id=chunk_id)
    if additional_context:
        prompt += f"\n\nAdditional Context:\n{additional_context}"
        
    model = get_llm_model()
    
    try:
        summary = _call_and_parse(prompt, model, evidence)
    except (LLMAPIError, LLMResponseError) as e:
        logger.error(f"Failed to summarize node {chunk_id or evidence.heading_path} after retries: {e}")
        raise SummarizationError(f"Node summarization failed: {e}", chunk_id=chunk_id)

    # Escalation logic: if insufficient evidence and we have full content, retry once
    if summary.insufficient_evidence:
        logger.warning(f"LLM returned insufficient_evidence for node {chunk_id or evidence.heading_path}")
        
        if summary.missing_concepts and full_content and not additional_context:
            logger.info(f"Escalation triggered for node {chunk_id or evidence.heading_path}")
            extra_context = handle_escalation(evidence, summary.missing_concepts, full_content)
            if extra_context:
                # Recursive call for escalation
                escalated_summary = summarize_node(
                    evidence, session, full_content, extra_context, chunk_id=chunk_id
                )
                # Aggregate token usage from escalation call
                if escalated_summary.token_usage and summary.token_usage:
                    escalated_summary.token_usage.input_tokens += summary.token_usage.input_tokens
                    escalated_summary.token_usage.output_tokens += summary.token_usage.output_tokens
                return escalated_summary
            else:
                logger.warning(f"No additional context found for missing concepts in node {chunk_id or evidence.heading_path}")
        
        # If we reach here, either escalation was already tried or no context found
        if additional_context:
            raise InsufficientEvidenceError(
                f"Insufficient evidence for node {chunk_id or evidence.heading_path} even after escalation",
                chunk_id=chunk_id
            )
            
    return summary
