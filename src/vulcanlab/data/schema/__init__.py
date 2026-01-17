"""
Schema module for database initialization.

Contains functions for creating enums, tables, indexes, triggers,
and specialized feature tables.
"""

from .enums import create_enums
from .tables import create_tables
from .indexes import (
    create_vector_indexes,
    create_fulltext_search,
    create_history_indexes,
)
from .triggers import (
    create_io_files_triggers,
    create_experiments_triggers,
    transfer_function_ownership,
    create_timestamp_trigger,
)
from .specialized_tables import (
    create_prompt_meta_table,
    create_result_models_table,
    create_default_rag_config,
    create_collections_table,
    create_research_tables,
    create_summarization_tables,
)

__all__ = [
    # Enums
    "create_enums",
    # Tables
    "create_tables",
    # Indexes
    "create_vector_indexes",
    "create_fulltext_search",
    "create_history_indexes",
    # Triggers
    "create_io_files_triggers",
    "create_experiments_triggers",
    "transfer_function_ownership",
    "create_timestamp_trigger",
    # Specialized tables
    "create_prompt_meta_table",
    "create_result_models_table",
    "create_default_rag_config",
    "create_collections_table",
    "create_research_tables",
    "create_summarization_tables",
]
