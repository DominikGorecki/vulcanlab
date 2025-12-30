"""
Core logic for automatic evaluation workflow.

This module provides the orchestration function for automatic evaluation mode,
where answer generation and judge evaluation are performed automatically
using different LLM providers.
"""

import logging
from typing import Dict

from sqlalchemy import func
from sqlalchemy.orm import Session

from vulcanlab.ai.config import LLMProvider, LLMSettings
from vulcanlab.ai.llm_factory import create_langchain_chat_for_provider
from vulcanlab.data.models.experiment import (
    Experiment,
    ExperimentPrompt,
    ExperimentAnswer,
)
from vulcanlab.eval.answers import create_answer_pair
from vulcanlab.eval.evaluations import generate_eval_prompt, submit_evaluation

logger = logging.getLogger(__name__)


def execute_automatic_eval(
    session: Session,
    experiment_id: int,
    main_prompt_text: str,
    answer_x_prompt_text: str,
    answer_y_prompt_text: str
) -> Dict:
    """
    Execute automatic evaluation workflow for an experiment.

    This function orchestrates the entire automatic evaluation workflow:
    1. Validate experiment has auto mode enabled
    2. Generate prompt_group_id
    3. Create three ExperimentPrompt records (main, answer_x, answer_y)
    4. Run answer_x_prompt with answer provider to generate answer_x
    5. Run answer_y_prompt with answer provider to generate answer_y
    6. Create ExperimentAnswer with both answers
    7. Generate evaluation prompt
    8. Run evaluation with judge provider
    9. Submit evaluation

    Args:
        session: Database session (must be passed explicitly).
        experiment_id: ID of the experiment to run automatic eval on.
        main_prompt_text: The main prompt text (for reference/grouping).
        answer_x_prompt_text: Prompt to generate answer_x.
        answer_y_prompt_text: Prompt to generate answer_y.

    Returns:
        Dict with keys:
            - evaluation_id: ID of created evaluation
            - answer_id: ID of created answer pair
            - prompt_group_id: Group ID linking the three prompts

    Raises:
        ValueError: If experiment not found or auto mode not enabled.
        Exception: If any step fails (LLM call, database operation, etc).
    """
    logger.info(
        f"Starting automatic eval for experiment_id={experiment_id}"
    )

    # 1. Load experiment and validate auto mode
    experiment = session.query(Experiment).filter(
        Experiment.id == experiment_id
    ).first()

    if not experiment:
        raise ValueError(f"Experiment with id {experiment_id} not found")

    if not experiment.auto_mode_enabled:
        raise ValueError(
            f"Automatic evaluation mode is not enabled for experiment {experiment_id}. "
            "Please enable auto mode first."
        )

    logger.info(
        f"Experiment {experiment_id} validated: "
        f"auto_mode_enabled=True, "
        f"answer_provider={experiment.auto_answer_provider}, "
        f"judge_provider={experiment.auto_judge_provider}"
    )

    # 2. Generate prompt_group_id (max + 1 for this experiment)
    max_group_id = session.query(
        func.max(ExperimentPrompt.prompt_group_id)
    ).filter(
        ExperimentPrompt.experiment_id == experiment_id
    ).scalar()

    prompt_group_id = (max_group_id or 0) + 1

    logger.info(f"Generated prompt_group_id={prompt_group_id} for experiment {experiment_id}")

    # 3. Create three ExperimentPrompt records with same prompt_group_id
    main_prompt = ExperimentPrompt(
        experiment_id=experiment_id,
        prompt_text=main_prompt_text.strip(),
        prompt_group_id=prompt_group_id
    )
    session.add(main_prompt)

    answer_x_prompt = ExperimentPrompt(
        experiment_id=experiment_id,
        prompt_text=answer_x_prompt_text.strip(),
        prompt_group_id=prompt_group_id
    )
    session.add(answer_x_prompt)

    answer_y_prompt = ExperimentPrompt(
        experiment_id=experiment_id,
        prompt_text=answer_y_prompt_text.strip(),
        prompt_group_id=prompt_group_id
    )
    session.add(answer_y_prompt)

    session.flush()  # Get IDs for logging

    logger.info(
        f"Created 3 prompts with prompt_group_id={prompt_group_id}: "
        f"main_id={main_prompt.id}, "
        f"answer_x_id={answer_x_prompt.id}, "
        f"answer_y_id={answer_y_prompt.id}"
    )

    # 4. Get LLM providers
    settings = LLMSettings()

    # Convert string provider names to LLMProvider enum
    answer_provider = LLMProvider(experiment.auto_answer_provider)
    judge_provider = LLMProvider(experiment.auto_judge_provider)

    logger.info(
        f"Using providers: answer_provider={answer_provider.value}, "
        f"judge_provider={judge_provider.value}"
    )

    # 5. Create LLM instances for answer provider (FULL tier)
    answer_llm_stack = create_langchain_chat_for_provider(
        provider=answer_provider,
        settings=settings,
        temperature=0.7  # Use higher temperature for more varied answers
    )
    answer_llm = answer_llm_stack.chat

    logger.info(
        f"Created answer LLM: provider={answer_provider.value}, "
        f"model={answer_llm.model_name if hasattr(answer_llm, 'model_name') else 'unknown'}"
    )

    # 6. Run answer_x_prompt with answer provider
    logger.info(f"Generating answer_x using {answer_provider.value}...")
    logger.info(f">>> CALLING LLM API for answer_x: provider={answer_provider.value}, prompt_length={len(answer_x_prompt_text)}")
    answer_x_response = answer_llm.invoke(answer_x_prompt_text)
    logger.info(f"<<< LLM API call COMPLETED for answer_x")
    # Handle content as string or list (newer LangChain versions may return list)
    answer_x_content = answer_x_response.content
    if isinstance(answer_x_content, list):
        # If list, extract text from content blocks
        answer_x_text = "".join(
            block.get("text", "") if isinstance(block, dict) else str(block)
            for block in answer_x_content
        ).strip()
    else:
        answer_x_text = answer_x_content.strip()

    logger.info(
        f"Generated answer_x: provider={answer_provider.value}, "
        f"length={len(answer_x_text)}, preview={answer_x_text[:100]}..."
    )

    # 7. Run answer_y_prompt with answer provider
    logger.info(f"Generating answer_y using {answer_provider.value}...")
    logger.info(f">>> CALLING LLM API for answer_y: provider={answer_provider.value}, prompt_length={len(answer_y_prompt_text)}")
    answer_y_response = answer_llm.invoke(answer_y_prompt_text)
    logger.info(f"<<< LLM API call COMPLETED for answer_y")
    # Handle content as string or list (newer LangChain versions may return list)
    answer_y_content = answer_y_response.content
    if isinstance(answer_y_content, list):
        # If list, extract text from content blocks
        answer_y_text = "".join(
            block.get("text", "") if isinstance(block, dict) else str(block)
            for block in answer_y_content
        ).strip()
    else:
        answer_y_text = answer_y_content.strip()

    logger.info(
        f"Generated answer_y: provider={answer_provider.value}, "
        f"length={len(answer_y_text)}, preview={answer_y_text[:100]}..."
    )

    # 8. Create ExperimentAnswer with randomized blind mapping
    answer = create_answer_pair(
        session=session,
        prompt_id=main_prompt.id,  # Link to main prompt
        answer_x=answer_x_text,
        answer_y=answer_y_text
    )

    logger.info(
        f"Created answer pair: answer_id={answer.id}, "
        f"prompt_id={main_prompt.id}, "
        f"is_x_mapped_to_a={answer.is_x_mapped_to_a}"
    )

    # 9. Generate evaluation prompt
    eval_prompt_text = generate_eval_prompt(session, answer.id)

    logger.info(
        f"Generated eval prompt: length={len(eval_prompt_text)}, "
        f"preview={eval_prompt_text[:150]}..."
    )

    # 10. Create LLM instance for judge provider (FULL tier)
    judge_llm_stack = create_langchain_chat_for_provider(
        provider=judge_provider,
        settings=settings,
        temperature=0.2  # Use lower temperature for consistent judging
    )
    judge_llm = judge_llm_stack.chat

    logger.info(
        f"Created judge LLM: provider={judge_provider.value}, "
        f"model={judge_llm.model_name if hasattr(judge_llm, 'model_name') else 'unknown'}"
    )

    # 11. Run evaluation with judge provider
    logger.info(f"Running evaluation using {judge_provider.value}...")
    logger.info(f">>> CALLING LLM API for judge: provider={judge_provider.value}, prompt_length={len(eval_prompt_text)}")
    judge_response = judge_llm.invoke(eval_prompt_text)
    logger.info(f"<<< LLM API call COMPLETED for judge")
    # Handle content as string or list (newer LangChain versions may return list)
    judge_content = judge_response.content
    if isinstance(judge_content, list):
        # If list, extract text from content blocks
        judge_text = "".join(
            block.get("text", "") if isinstance(block, dict) else str(block)
            for block in judge_content
        ).strip()
    else:
        judge_text = judge_content.strip()

    logger.info(
        f"Received judge response: provider={judge_provider.value}, "
        f"length={len(judge_text)}, preview={judge_text[:150]}..."
    )

    # 12. Parse judge response
    # Expected format from eval template:
    # OVERALL_SCORE: <number>
    # DIMENSION_SCORES: <json>
    # JUSTIFICATION: <text>
    overall_score, dimension_scores, justification = _parse_judge_response(judge_text)

    logger.info(
        f"Parsed judge response: overall_score={overall_score}, "
        f"dimensions={list(dimension_scores.keys())}"
    )

    # 13. Submit evaluation
    evaluation = submit_evaluation(
        session=session,
        answer_id=answer.id,
        overall_score=overall_score,
        justification=justification,
        dimension_scores=dimension_scores
    )

    logger.info(
        f"Submitted evaluation: evaluation_id={evaluation.id}, "
        f"answer_id={answer.id}, overall_score={overall_score}"
    )

    # 14. Return result
    result = {
        "evaluation_id": evaluation.id,
        "answer_id": answer.id,
        "prompt_group_id": prompt_group_id
    }

    logger.info(
        f"Automatic eval completed successfully for experiment {experiment_id}: "
        f"evaluation_id={evaluation.id}, answer_id={answer.id}, "
        f"prompt_group_id={prompt_group_id}"
    )

    return result


def _parse_judge_response(judge_text: str) -> tuple[int, Dict[str, int], str]:
    """
    Parse the judge LLM response to extract scores and justification.

    Supports two formats:
    1. Labeled format:
        OVERALL_SCORE: 5
        DIMENSION_SCORES: {"factual_correctness": 6, "clarity": 4, ...}
        JUSTIFICATION: Answer A is better because...

    2. JSON format:
        {
          "overall_score": 5,
          "dimension_scores": {"factual_correctness": 6, ...},
          "justification": "Answer A is better..."
        }

    Args:
        judge_text: Raw response from judge LLM.

    Returns:
        Tuple of (overall_score, dimension_scores, justification).

    Raises:
        ValueError: If response format is invalid or cannot be parsed.
    """
    import json
    import re

    judge_text = judge_text.strip()

    # Try to parse as JSON first
    try:
        data = json.loads(judge_text)
        # Extract fields from JSON (handle both snake_case and lowercase)
        overall_score = data.get("overall_score") or data.get("OVERALL_SCORE")
        dimension_scores = data.get("dimension_scores") or data.get("DIMENSION_SCORES")
        justification = data.get("justification") or data.get("JUSTIFICATION")

        # Validate all fields are present
        if overall_score is None:
            raise ValueError("overall_score field missing in JSON response")
        if not dimension_scores:
            raise ValueError("dimension_scores field missing or empty in JSON response")
        if not justification:
            raise ValueError("justification field missing in JSON response")

        # Validate types
        if not isinstance(overall_score, int):
            raise ValueError(f"overall_score must be an integer, got {type(overall_score)}")
        if not isinstance(dimension_scores, dict):
            raise ValueError(f"dimension_scores must be a dict, got {type(dimension_scores)}")
        if not all(isinstance(v, int) for v in dimension_scores.values()):
            raise ValueError("All dimension scores must be integers")

        return overall_score, dimension_scores, justification

    except json.JSONDecodeError:
        # Not JSON, try labeled format
        pass

    # Parse labeled format (line by line)
    lines = judge_text.split('\n')
    overall_score = None
    dimension_scores = {}
    justification = ""

    for i, line in enumerate(lines):
        line = line.strip()

        # Parse OVERALL_SCORE
        if line.startswith("OVERALL_SCORE:"):
            score_str = line.split(":", 1)[1].strip()
            try:
                overall_score = int(score_str)
            except ValueError:
                raise ValueError(f"Invalid OVERALL_SCORE format: {score_str}")

        # Parse DIMENSION_SCORES
        elif line.startswith("DIMENSION_SCORES:"):
            json_str = line.split(":", 1)[1].strip()
            try:
                dimension_scores = json.loads(json_str)
                # Validate all values are integers
                if not all(isinstance(v, int) for v in dimension_scores.values()):
                    raise ValueError("All dimension scores must be integers")
            except (json.JSONDecodeError, ValueError) as e:
                raise ValueError(f"Invalid DIMENSION_SCORES format: {e}")

        # Parse JUSTIFICATION (rest of the text after the label)
        elif line.startswith("JUSTIFICATION:"):
            # Get everything after "JUSTIFICATION:" including subsequent lines
            justification_start = i
            justification_parts = [line.split(":", 1)[1].strip()]
            # Add remaining lines as justification
            justification_parts.extend(lines[justification_start + 1:])
            justification = "\n".join(justification_parts).strip()
            break  # No more parsing needed

    # Validate we got all required fields
    if overall_score is None:
        raise ValueError("OVERALL_SCORE not found in judge response")

    if not dimension_scores:
        raise ValueError("DIMENSION_SCORES not found or empty in judge response")

    if not justification:
        raise ValueError("JUSTIFICATION not found in judge response")

    return overall_score, dimension_scores, justification
