"""
Template resolution utilities for evaluation prompts.

This module provides functions for resolving evaluation prompt templates
with placeholder substitution.
"""

import logging
from sqlalchemy.orm import Session
from typing import Optional

from vulcanlab.data.models.prompt_template import PromptTemplate

logger = logging.getLogger(__name__)

# Fallback template if database lookup fails
FALLBACK_EVAL_TEMPLATE = """Please evaluate the following pair of answers to the given prompt. Compare Answer A and Answer B based on the 5 core dimensions.

PROMPT:
{prompt}

ANSWER A:
{answer_a}

ANSWER B:
{answer_b}

REQUIRED DIMENSIONS:
1. factual_correctness - Accuracy of information and facts
2. completeness - Coverage of all relevant aspects
3. coherence - Logical flow and organization
4. hallucination_risk - Presence of unsupported or fabricated information
5. academic_response - Appropriate academic tone and rigor

Evaluate these answers and provide:
- An overall score from -10 to +10 (where -10 means B is much better, 0 means tie, +10 means A is much better)
- Scores for each dimension from -10 to +10 (same scale)
- A justification explaining your evaluation

Respond with valid JSON in this exact format:
{{
  "overall_score": <integer from -10 to 10>,
  "justification": "<your detailed explanation>",
  "dimension_scores": {{
    "factual_correctness": <integer from -10 to 10>,
    "completeness": <integer from -10 to 10>,
    "coherence": <integer from -10 to 10>,
    "hallucination_risk": <integer from -10 to 10>,
    "academic_response": <integer from -10 to 10>
  }}
}}"""


def resolve_eval_template(
    template_text: str,
    prompt: str,
    answer_a: str,
    answer_b: str
) -> str:
    """
    Resolve evaluation template by substituting placeholders.

    Replaces {prompt}, {answer_a}, and {answer_b} placeholders with actual values.

    Args:
        template_text: Template string with placeholders.
        prompt: The prompt text to substitute.
        answer_a: Answer A text to substitute.
        answer_b: Answer B text to substitute.

    Returns:
        Resolved template with placeholders replaced.

    Raises:
        ValueError: If any required placeholder is missing in template.
    """
    # Validate template has required placeholders
    required_placeholders = ['{prompt}', '{answer_a}', '{answer_b}']
    missing = [p for p in required_placeholders if p not in template_text]

    if missing:
        raise ValueError(
            f"Template missing required placeholders: {', '.join(missing)}"
        )

    # Perform substitution
    resolved = template_text.format(
        prompt=prompt,
        answer_a=answer_a,
        answer_b=answer_b
    )

    logger.debug(
        f"Resolved eval template: prompt_len={len(prompt)}, "
        f"answer_a_len={len(answer_a)}, answer_b_len={len(answer_b)}, "
        f"result_len={len(resolved)}"
    )

    return resolved


def get_default_template(session: Optional[Session] = None) -> str:
    """
    Get the default evaluation template.

    Attempts to load the default template from the database (function_tag='eval_default').
    Falls back to a hardcoded template if database is unavailable or template not found.

    Args:
        session: Optional database session. If not provided, uses fallback template.

    Returns:
        Default evaluation template string.
    """
    if session:
        try:
            # Try to load eval_default template from database
            template = session.query(PromptTemplate).filter(
                PromptTemplate.function_tag == "eval_default",
                PromptTemplate.is_active == True
            ).order_by(PromptTemplate.version.desc()).first()

            if template:
                logger.info(
                    f"Using default eval template from database: "
                    f"function_tag='eval_default', version={template.version}, id={template.id}"
                )
                return template.template_content
            else:
                logger.warning(
                    "Default eval template (function_tag='eval_default') not found in database. "
                    "Using fallback template. Have you run the seed script?"
                )
        except Exception as e:
            logger.error(f"Error loading default template from database: {e}. Using fallback.")
    else:
        logger.debug("No session provided to get_default_template(), using fallback template")

    return FALLBACK_EVAL_TEMPLATE
