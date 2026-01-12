"""
Research module for deep research workflows.

Provides research planning, execution, and synthesis functionality.
"""

from .research_planner import (
    ResearchPlan,
    SubQuestion,
    analyze_collection,
    generate_research_plan,
    validate_research_plan,
)

__all__ = [
    "ResearchPlan",
    "SubQuestion",
    "analyze_collection",
    "generate_research_plan",
    "validate_research_plan",
]
