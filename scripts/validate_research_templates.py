#!/usr/bin/env python3
"""
Validate research template migration.
Run this before deploying to ensure templates are correctly configured.
"""

import sys
from pathlib import Path

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from vulcanlab.data.template_loader import load_template
from vulcanlab.data.database import get_session
from vulcanlab.data.models.prompt_template import PromptTemplate


def validate_research_templates():
    """Validate all research templates are loadable and have correct variables."""

    templates_config = {
        "research_planning": [
            "name", "description", "tags", "item_count",
            "excerpt_count", "research_result_count", "query_count", "items_list"
        ],
        "section_synthesis": ["question_text", "context", "sources_list"],
        "synthesis": ["research_goal", "section_contents"],
        "quality_evaluation": ["content", "sources_list"]
    }

    errors = []

    print("Validating research templates...\n")

    for function_tag, expected_vars in templates_config.items():
        try:
            # Load from DB
            template = load_template(function_tag, fallback_builder=None)

            # Verify it's a LangChain template
            if not hasattr(template, 'format'):
                errors.append(f"{function_tag}: Not a valid LangChain PromptTemplate")
                continue

            # Verify input variables match expected
            actual_vars = set(template.input_variables)
            expected_vars_set = set(expected_vars)

            if actual_vars != expected_vars_set:
                missing = expected_vars_set - actual_vars
                extra = actual_vars - expected_vars_set
                msg = f"{function_tag}: Variable mismatch."
                if missing:
                    msg += f" Missing: {missing}."
                if extra:
                    msg += f" Extra: {extra}."
                errors.append(msg)
            else:
                print(f"✓ {function_tag}: OK ({len(actual_vars)} variables)")

        except Exception as e:
            errors.append(f"{function_tag}: {str(e)}")

    # Check unused templates are NOT in DB
    print("\nVerifying unused templates are excluded...\n")

    with get_session() as session:
        unused_templates = ["section_generation", "context_assembly_new",
                           "context_assembly_ensemble", "result_matching"]

        for function_tag in unused_templates:
            found = session.query(PromptTemplate).filter(
                PromptTemplate.function_tag == function_tag,
                PromptTemplate.is_active == True
            ).first()

            if found:
                errors.append(f"{function_tag}: Should NOT be active in database")
            else:
                print(f"✓ {function_tag}: Correctly excluded")

    if errors:
        print("\n❌ VALIDATION FAILED:")
        for error in errors:
            print(f"  - {error}")
        return False
    else:
        print("\n✅ All templates validated successfully")
        return True


if __name__ == "__main__":
    success = validate_research_templates()
    sys.exit(0 if success else 1)
