"""
Template resolution utilities for evaluation prompts.

This module provides functions for resolving evaluation prompt templates
with placeholder substitution.
"""

import logging

logger = logging.getLogger(__name__)

# Hardcoded template for T04 - will be replaced with database templates in T06
HARDCODED_EVAL_TEMPLATE = """Please evaluate the following pair of answers to the given prompt. Compare Answer A and Answer B based on the specified dimensions.

PROMPT:
{prompt}

ANSWER A:
{answer_a}

ANSWER B:
{answer_b}

Evaluate these answers and provide:
1. An overall score from -10 to +10 (where -10 means B is much better, 0 means tie, +10 means A is much better)
2. Scores for each dimension from -10 to +10 (same scale)
3. A justification explaining your evaluation

Respond with valid JSON in this exact format:
{{
  "overall_score": <integer from -10 to 10>,
  "justification": "<your explanation>",
  "dimension_scores": {{
    "dimension_name": <integer from -10 to 10>
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


def get_default_template() -> str:
    """
    Get the default hardcoded evaluation template.

    Returns:
        Default evaluation template string.
    """
    return HARDCODED_EVAL_TEMPLATE
