"""
Seed evaluation prompt templates into the database.

This module contains default eval templates for the evaluation system.
"""

from typing import List, Dict, Any
from sqlalchemy import text
from sqlalchemy.exc import IntegrityError

from .database import engine

# Default evaluation template
EVAL_TEMPLATES: List[Dict[str, Any]] = [
    {
        "function_tag": "eval_default",
        "template_type": "eval",
        "version": 1,
        "title": "Default Evaluation Template - Comparative Scoring",
        "template_content": """Please evaluate the following pair of answers to the given prompt. Compare Answer A and Answer B **blindly**, based only on their content and quality relative to the prompt. Do not assume how the answers were generated.

PROMPT:
{prompt}

ANSWER A:
{answer_a}

ANSWER B:
{answer_b}

---

EVALUATION INSTRUCTIONS

You must compare Answer A and Answer B using a **signed numeric comparison scale**.

SCORING SCALE (use integers only):
+10 = Answer A is much better
+5 = Answer A is moderately better
+1 = Answer A is slightly better
0 = No meaningful difference
-1 = Answer B is slightly better
-5 = Answer B is moderately better
-10 = Answer B is much better

Use extreme values (±10) only when the difference is clear and decisive.
Default to 0 when differences are small, unclear, or mixed.

---

EVALUATION DIMENSIONS

Score each dimension **relative to the other answer**, not absolutely.

1. factual_correctness
   Accuracy of claims and absence of clear factual errors or contradictions.

2. completeness
   Degree to which the answer fully and appropriately addresses the prompt.

3. coherence
   Logical structure, clarity, and internal consistency of reasoning.

4. hallucination_risk
   Degree to which the answer makes unsupported, speculative, or overconfident claims.
   (Lower hallucination risk should score higher.)

5. academic_response
   Degree to which the answer reflects expert-level or academically appropriate reasoning, including:

   * precise terminology
   * appropriate qualification and uncertainty
   * avoidance of oversimplification
   * structured argument when appropriate

---

IMPORTANT RULES

* Evaluate answers **relative to each other**, not on an absolute quality scale.
* Do NOT reward verbosity unless it improves correctness or clarity.
* Do NOT assume access to external sources or retrieved context.
* Penalize confident claims that appear unjustified or overly general.
* If both answers have similar strengths and weaknesses, score 0.

---

Respond with valid JSON in this exact format:
{{
"overall_score": <integer from -10 to 10>,
"justification": "<concise explanation citing specific differences between Answer A and Answer B>",
"dimension_scores": {{
"factual_correctness": <integer from -10 to 10>,
"completeness": <integer from -10 to 10>,
"coherence": <integer from -10 to 10>,
"hallucination_risk": <integer from -10 to 10>,
"academic_response": <integer from -10 to 10>
}}
}}

        """,
        "is_active": True,
    }
]


def seed_eval_templates(verbose: bool = False) -> None:
    """Seed the database with default evaluation templates."""
    if verbose:
        print("Seeding evaluation templates...")

    with engine.connect() as conn:
        for template_data in EVAL_TEMPLATES:
            # Check if template already exists
            result = conn.execute(
                text("""
                    SELECT COUNT(*) FROM prompt_templates
                    WHERE function_tag = :function_tag AND version = :version
                """),
                {
                    "function_tag": template_data["function_tag"],
                    "version": template_data["version"]
                }
            )
            count = result.scalar()

            if count > 0:
                if verbose:
                    print(f"  Template '{template_data['function_tag']}' already exists")
                continue

            # Insert the template
            try:
                conn.execute(
                    text("""
                        INSERT INTO prompt_templates
                        (function_tag, template_type, version, title, template_content, is_active, created_at, updated_at)
                        VALUES (:function_tag, :template_type, :version, :title, :template_content, :is_active, NOW(), NOW())
                    """),
                    template_data
                )
                conn.commit()

                if verbose:
                    print(f"  ✓ Inserted eval template: {template_data['title']}")

            except IntegrityError as e:
                if verbose:
                    print(f"  Warning: Could not insert template: {e}")
                conn.rollback()

    if verbose:
        print("Eval template seeding complete")


if __name__ == "__main__":
    seed_eval_templates(verbose=True)
