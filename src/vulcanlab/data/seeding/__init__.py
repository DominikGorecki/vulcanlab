"""
Seeding module for database initialization.

Contains functions for seeding initial data into the database,
including prompt templates and default configuration values.
"""

from .prompt_templates import seed_prompt_templates, seed_simple_conversion_templates
from .defaults import seed_default_result_model

__all__ = [
    "seed_prompt_templates",
    "seed_simple_conversion_templates",
    "seed_default_result_model",
]
