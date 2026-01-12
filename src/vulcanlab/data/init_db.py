"""
Database initialization script.

Database configuration (host, port, users) loaded from vulcanlab.config.json.
Passwords (secrets) loaded from .env file.

Example (as script):
    venv\\Scripts\\python -m vulcanlab.data.init_db

Example (as library):
    from vulcanlab.data.init_db import init_database
    init_database()
"""

import argparse
import sys

# Import all models to register them with Base
from .models import (  # noqa: F401
    Chunk,
    Query,
    Result,
    ResultModel,
    Work,
    RagConfig,
    Collection,
    CollectionItem,
    ResearchSession,
    ResearchSection,
    ResearchReport,
)
from .models.io_file import IOFile  # noqa: F401
from .models.prompt_template import PromptTemplate  # noqa: F401
from .models.prompt_meta import PromptMeta  # noqa: F401
from .models.parsed_markdown import ParsedMarkdown  # noqa: F401
from .models.sanitized_markdown import SanitizedMarkdown  # noqa: F401
from .models.heading_modifications import HeadingModification  # noqa: F401
from .models.experiment import (  # noqa: F401
    Experiment,
    ExperimentDimension,
    ExperimentPrompt,
    ExperimentAnswer,
    ExperimentEvaluation,
    ExperimentDimensionResult,
)

# Import initialization functions from modules
from .database_setup import create_database_and_user, enable_pgvector_extension
from .schema import (
    create_enums,
    create_tables,
    create_io_files_triggers,
    create_experiments_triggers,
    create_vector_indexes,
    create_fulltext_search,
    create_history_indexes,
    create_prompt_meta_table,
    create_result_models_table,
    create_default_rag_config,
    create_collections_table,
    create_research_tables,
)
from .seeding import seed_prompt_templates, seed_default_result_model


def init_database(verbose: bool = False) -> None:
    """
    Initialize the database: create database, user, tables, and indexes.

    Args:
        verbose: If True, print progress information.
    """
    # Phase 1: Database and user setup
    create_database_and_user(verbose=verbose)
    enable_pgvector_extension(verbose=verbose)

    # Phase 2: Schema setup
    create_enums(verbose=verbose)
    create_tables(verbose=verbose)

    # Phase 3: Triggers for ORM tables
    create_io_files_triggers(verbose=verbose)
    create_experiments_triggers(verbose=verbose)

    # Phase 4: Indexes
    create_vector_indexes(verbose=verbose)
    create_fulltext_search(verbose=verbose)
    create_history_indexes(verbose=verbose)

    # Phase 5: Specialized tables with their own triggers/indexes
    create_prompt_meta_table(verbose=verbose)
    create_result_models_table(verbose=verbose)
    create_collections_table(verbose=verbose)
    create_research_tables(verbose=verbose)

    # Phase 6: Seed data
    seed_prompt_templates(verbose=verbose)
    seed_default_result_model(verbose=verbose)
    create_default_rag_config(verbose=verbose)

    if verbose:
        print("Database initialization complete")


def main() -> int:
    """
    Main entry point for the command-line interface.

    Returns:
        Exit code (0 for success, 1 for error).
    """
    parser = argparse.ArgumentParser(
        description="Initialize VulcanLab database.",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  %(prog)s              # Initialize database
  %(prog)s -v           # Verbose output
        """
    )

    parser.add_argument(
        "-v", "--verbose",
        action="store_true",
        help="Print progress information"
    )

    args = parser.parse_args()

    try:
        init_database(verbose=args.verbose)
        return 0
    except Exception as e:
        print(f"Database initialization failed: {e}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    sys.exit(main())
