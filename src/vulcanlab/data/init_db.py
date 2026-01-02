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
import os
from pathlib import Path

import yaml
from dotenv import load_dotenv
from sqlalchemy import create_engine, text
from sqlalchemy.exc import ProgrammingError

from vulcanlab.config import load_config
from .database import Base, engine, get_admin_database_url
from .env_utils import get_required_env_var

# Import all models to register them with Base
from .models import Chunk, Query, Result, ResultModel, Work, RagConfig  # noqa: F401
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

# Import seeding functions
from .seed_templates import seed_prompt_templates


def create_database_and_user(verbose: bool = False) -> None:
    """
    Create the database and application user if they don't exist.

    Args:
        verbose: If True, print progress information.
    """
    load_dotenv()

    # Load config from JSON
    db_config = load_config().database

    db_name = db_config.db_name
    app_user = db_config.app_user
    app_password = get_required_env_var("POSTGRES_APP_PASSWORD", "Application database password")

    admin_url = get_admin_database_url()
    admin_engine = create_engine(
        admin_url,
        isolation_level="AUTOCOMMIT",
        connect_args={
            "prepare_threshold": None,
            "options": "-c client_encoding=UTF8"
        },
        pool_pre_ping=True
    )

    with admin_engine.connect() as conn:
        # Check if database exists
        result = conn.execute(
            text("SELECT 1 FROM pg_database WHERE datname = :db_name"),
            {"db_name": db_name}
        )
        db_exists = result.fetchone() is not None

        if not db_exists:
            if verbose:
                print(f"Creating database: {db_name}")
            conn.execute(text(f'CREATE DATABASE "{db_name}"'))
        else:
            if verbose:
                print(f"Database already exists: {db_name}")

        # Check if user exists
        result = conn.execute(
            text("SELECT 1 FROM pg_roles WHERE rolname = :username"),
            {"username": app_user}
        )
        user_exists = result.fetchone() is not None

        if not user_exists:
            if verbose:
                print(f"Creating user: {app_user}")
            # Password must be escaped as a literal since CREATE USER doesn't support parameters
            escaped_password = app_password.replace("'", "''")
            conn.execute(
                text(f"CREATE USER \"{app_user}\" WITH PASSWORD '{escaped_password}'")
            )
        else:
            if verbose:
                print(f"User already exists: {app_user}")

    # Grant privileges (connect to the specific database)
    admin_password = get_required_env_var("POSTGRES_ADMIN_PASSWORD", "Admin database password")
    db_url = (
        f"postgresql+psycopg://{db_config.admin_user}:"
        f"{admin_password}"
        f"@{db_config.host}:"
        f"{db_config.port}/{db_name}"
    )
    db_engine = create_engine(
        db_url,
        isolation_level="AUTOCOMMIT",
        connect_args={
            "prepare_threshold": None,
            "options": "-c client_encoding=UTF8"
        },
        pool_pre_ping=True
    )

    with db_engine.connect() as conn:
        if verbose:
            print(f"Granting privileges to {app_user} on {db_name}")

        # Grant all privileges on database
        conn.execute(text(f'GRANT ALL PRIVILEGES ON DATABASE "{db_name}" TO "{app_user}"'))

        # Grant schema privileges
        conn.execute(text(f'GRANT ALL ON SCHEMA public TO "{app_user}"'))

        # Grant privileges on all tables (current and future)
        conn.execute(
            text(f'ALTER DEFAULT PRIVILEGES IN SCHEMA public GRANT ALL ON TABLES TO "{app_user}"')
        )
        conn.execute(
            text(f'ALTER DEFAULT PRIVILEGES IN SCHEMA public GRANT ALL ON SEQUENCES TO "{app_user}"')
        )


def enable_pgvector_extension(verbose: bool = False) -> None:
    """
    Enable the pgvector extension in the database.

    Args:
        verbose: If True, print progress information.
    """
    if verbose:
        print("Enabling pgvector extension...")

    # Need admin privileges to create extensions
    db_config = load_config().database
    db_name = db_config.db_name
    admin_password = get_required_env_var("POSTGRES_ADMIN_PASSWORD", "Admin database password")
    db_url = (
        f"postgresql+psycopg://{db_config.admin_user}:"
        f"{admin_password}"
        f"@{db_config.host}:"
        f"{db_config.port}/{db_name}"
    )
    admin_engine = create_engine(
        db_url,
        isolation_level="AUTOCOMMIT",
        connect_args={
            "prepare_threshold": None,
            "options": "-c client_encoding=UTF8"
        },
        pool_pre_ping=True
    )

    with admin_engine.connect() as conn:
        conn.execute(text("CREATE EXTENSION IF NOT EXISTS vector"))

    if verbose:
        print("pgvector extension enabled")


def create_enums(verbose: bool = False) -> None:
    """
    Create custom enum types required by the models.

    This ensures all enum values are present even if migrations were run
    that created incomplete enum types.

    Args:
        verbose: If True, print progress information.
    """
    if verbose:
        print("Creating enum types...")

    with engine.connect() as conn:
        # Create filetype enum for io_files table (matching working database)
        conn.execute(text("""
            DO $$ BEGIN
                CREATE TYPE filetype AS ENUM ('INPUT', 'TO_CONVERT');
            EXCEPTION
                WHEN duplicate_object THEN NULL;
            END $$;
        """))

        # Create file_type enum with all values
        conn.execute(text("""
            DO $$ BEGIN
                CREATE TYPE file_type AS ENUM ('pdf', 'epub', 'markdown_import');
            EXCEPTION
                WHEN duplicate_object THEN
                    -- Enum exists, check if markdown_import value is present
                    BEGIN
                        -- Try to add markdown_import if it doesn't exist
                        ALTER TYPE file_type ADD VALUE IF NOT EXISTS 'markdown_import';
                    EXCEPTION
                        WHEN OTHERS THEN NULL;
                    END;
            END $$;
        """))

        # Create document_classification enum
        conn.execute(text("""
            DO $$ BEGIN
                CREATE TYPE document_classification AS ENUM ('small', 'large');
            EXCEPTION
                WHEN duplicate_object THEN NULL;
            END $$;
        """))

        # Create modification_action enum
        conn.execute(text("""
            DO $$ BEGIN
                CREATE TYPE modification_action AS ENUM ('remove', 'change', 'keep');
            EXCEPTION
                WHEN duplicate_object THEN NULL;
            END $$;
        """))

        conn.commit()

    if verbose:
        print("Enum types created successfully")


def create_tables(verbose: bool = False) -> None:
    """
    Create all tables defined in the models.

    Args:
        verbose: If True, print progress information.
    """
    if verbose:
        print("Creating tables...")

    Base.metadata.create_all(bind=engine)

    if verbose:
        print("Tables created successfully")


def create_io_files_triggers(verbose: bool = False) -> None:
    """
    Create triggers for io_files table.

    The table itself is created by SQLAlchemy's create_all(), but we need
    to manually add the trigger for automatically updating the updated_at column.

    Args:
        verbose: If True, print progress information.
    """
    if verbose:
        print("Creating io_files triggers...")

    with engine.connect() as conn:
        # Create trigger function to automatically update updated_at timestamp
        conn.execute(text("""
            CREATE OR REPLACE FUNCTION update_io_files_updated_at()
            RETURNS TRIGGER AS $$
            BEGIN
                NEW.updated_at = NOW();
                RETURN NEW;
            END;
            $$ LANGUAGE plpgsql
        """))

        # Create trigger
        conn.execute(text("DROP TRIGGER IF EXISTS trigger_update_io_files_updated_at ON io_files"))
        conn.execute(text("""
            CREATE TRIGGER trigger_update_io_files_updated_at
                BEFORE UPDATE ON io_files
                FOR EACH ROW
                EXECUTE FUNCTION update_io_files_updated_at()
        """))

        conn.commit()

    # Transfer ownership to app user
    db_config = load_config().database
    app_user = db_config.app_user

    try:
        with engine.connect() as conn:
            conn.execute(text(f'ALTER FUNCTION update_io_files_updated_at() OWNER TO "{app_user}"'))
            conn.commit()
            if verbose:
                print(f"Transferred ownership of io_files trigger function to {app_user}")
    except Exception as e:
        if verbose:
            print(f"Note: Could not transfer ownership (this is okay if running as app user): {e}")

    if verbose:
        print("io_files triggers created successfully")


def create_vector_indexes(verbose: bool = False) -> None:
    """
    Create HNSW indexes for vector columns and other chunk optimization indexes.

    Args:
        verbose: If True, print progress information.
    """
    if verbose:
        print("Creating vector indexes...")

    with engine.connect() as conn:
        # Create HNSW index for cosine similarity on chunks.embedding
        conn.execute(text("""
            CREATE INDEX IF NOT EXISTS ix_chunks_embedding_hnsw
            ON chunks USING hnsw (embedding vector_cosine_ops)
        """))

        # Create HNSW indexes for queries table embeddings
        conn.execute(text("""
            CREATE INDEX IF NOT EXISTS ix_queries_embedding_original_hnsw
            ON queries USING hnsw (embedding_original vector_cosine_ops)
        """))
        conn.execute(text("""
            CREATE INDEX IF NOT EXISTS ix_queries_embedding_hyde_hnsw
            ON queries USING hnsw (embedding_hyde vector_cosine_ops)
        """))

        # Create index on sentence_count for filtering (migration 019)
        conn.execute(text("""
            CREATE INDEX IF NOT EXISTS idx_chunks_sentence_count
            ON chunks (sentence_count)
        """))

        conn.commit()

    if verbose:
        print("Vector indexes created successfully")


def create_fulltext_search(verbose: bool = False) -> None:
    """
    Create full-text search infrastructure for chunks.

    This adds tsvector column, GIN index, and auto-update trigger.

    Args:
        verbose: If True, print progress information.
    """
    if verbose:
        print("Creating full-text search infrastructure...")

    with engine.connect() as conn:
        # Add tsvector column
        conn.execute(text("""
            ALTER TABLE chunks ADD COLUMN IF NOT EXISTS content_tsvector tsvector
        """))

        # Create GIN index for full-text search
        conn.execute(text("""
            CREATE INDEX IF NOT EXISTS ix_chunks_content_tsvector_gin
            ON chunks USING gin (content_tsvector)
        """))

        # Create trigger function
        conn.execute(text("""
            CREATE OR REPLACE FUNCTION chunks_content_tsvector_trigger()
            RETURNS trigger AS $$
            BEGIN
                NEW.content_tsvector := to_tsvector('english', COALESCE(NEW.content, ''));
                RETURN NEW;
            END;
            $$ LANGUAGE plpgsql
        """))

        # Create trigger (drop first to avoid duplicates)
        conn.execute(text("DROP TRIGGER IF EXISTS tsvector_update ON chunks"))
        conn.execute(text("""
            CREATE TRIGGER tsvector_update
            BEFORE INSERT OR UPDATE OF content ON chunks
            FOR EACH ROW
            EXECUTE FUNCTION chunks_content_tsvector_trigger()
        """))

        conn.commit()

    # Transfer ownership to app user
    db_config = load_config().database
    app_user = db_config.app_user

    try:
        with engine.connect() as conn:
            conn.execute(text(f'ALTER FUNCTION chunks_content_tsvector_trigger() OWNER TO "{app_user}"'))
            conn.commit()
            if verbose:
                print(f"Transferred ownership of full-text search function to {app_user}")
    except Exception as e:
        if verbose:
            print(f"Note: Could not transfer ownership (this is okay if running as app user): {e}")

    if verbose:
        print("Full-text search infrastructure created successfully")


def create_history_indexes(verbose: bool = False) -> None:
    """
    Create indexes for efficient history query operations.

    This creates two indexes on the works table:
    1. General timestamp index for sorting all works by created_at
    2. Partial index for filtering simple conversion works with timestamp sorting
    3. GIN index on processing_status JSONB for efficient JSON queries

    The partial index only includes works with simple_conversion_mode in their
    processing_status JSON, making it more efficient for simple conversion queries.

    Args:
        verbose: If True, print progress information.
    """
    if verbose:
        print("Creating history query indexes...")

    with engine.connect() as conn:
        # Create GIN index on processing_status for JSONB operations (migration 008)
        conn.execute(text("""
            CREATE INDEX IF NOT EXISTS ix_works_processing_status_gin
            ON works USING gin (processing_status)
        """))

        # Create general timestamp index for sorting all works
        conn.execute(text("""
            CREATE INDEX IF NOT EXISTS ix_works_created_at
            ON works (created_at DESC)
        """))

        # Create partial index for simple conversion works
        # Only indexes works where processing_status contains 'simple_conversion_mode' key
        conn.execute(text("""
            CREATE INDEX IF NOT EXISTS ix_works_simple_conversion_created_at
            ON works (created_at DESC)
            WHERE (processing_status ? 'simple_conversion_mode')
        """))

        conn.commit()

    if verbose:
        print("History query indexes created successfully")


def create_prompt_meta_table(verbose: bool = False) -> None:
    """
    Create prompt_meta table for storing prompt template metadata.

    This table stores variable descriptions and other metadata for prompt templates,
    with one record per function_tag.

    Args:
        verbose: If True, print progress information.
    """
    if verbose:
        print("Creating prompt_meta table...")

    with engine.connect() as conn:
        # Create prompt_meta table
        conn.execute(text("""
            CREATE TABLE IF NOT EXISTS prompt_meta (
                id SERIAL PRIMARY KEY,
                function_tag VARCHAR(100) UNIQUE NOT NULL,
                variables JSONB NOT NULL DEFAULT '[]'::jsonb,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """))

        # Create index on function_tag for efficient lookups
        conn.execute(text("""
            CREATE INDEX IF NOT EXISTS idx_prompt_meta_function_tag
            ON prompt_meta(function_tag)
        """))

        # Create trigger function for updated_at
        conn.execute(text("""
            CREATE OR REPLACE FUNCTION update_prompt_meta_updated_at()
            RETURNS TRIGGER AS $$
            BEGIN
                NEW.updated_at = CURRENT_TIMESTAMP;
                RETURN NEW;
            END;
            $$ LANGUAGE plpgsql
        """))

        # Create trigger
        conn.execute(text("DROP TRIGGER IF EXISTS trigger_update_prompt_meta_updated_at ON prompt_meta"))
        conn.execute(text("""
            CREATE TRIGGER trigger_update_prompt_meta_updated_at
                BEFORE UPDATE ON prompt_meta
                FOR EACH ROW
                EXECUTE FUNCTION update_prompt_meta_updated_at()
        """))

        conn.commit()

    # Transfer ownership to app user
    db_config = load_config().database
    app_user = db_config.app_user

    try:
        with engine.connect() as conn:
            conn.execute(text(f'ALTER FUNCTION update_prompt_meta_updated_at() OWNER TO "{app_user}"'))
            conn.execute(text(f'ALTER SEQUENCE IF EXISTS prompt_meta_id_seq OWNER TO "{app_user}"'))
            conn.commit()
            if verbose:
                print(f"Transferred ownership of prompt_meta objects to {app_user}")
    except Exception as e:
        if verbose:
            print(f"Note: Could not transfer ownership (this is okay if running as app user): {e}")

    if verbose:
        print("prompt_meta table created successfully")


def seed_prompt_templates(verbose: bool = False) -> None:
    """
    Seed all prompt templates from YAML config and individual template files.

    Reads templates.yaml configuration and loads template content from
    individual .txt files in the seed_data/templates/ directory.

    Also seeds prompt_meta (variable definitions) from variables.yaml.

    This replaces the old hardcoded SQL approach and allows easy modification
    of templates by editing the .txt files.
    """
    if verbose:
        print("Seeding prompt templates from configuration files...")

    # Get path to templates directory
    seed_data_dir = Path(__file__).parent / "seed_data"
    templates_config_path = seed_data_dir / "templates.yaml"
    variables_config_path = seed_data_dir / "variables.yaml"
    templates_dir = seed_data_dir / "templates"

    # Load templates configuration
    if not templates_config_path.exists():
        if verbose:
            print(f"Warning: templates.yaml not found at {templates_config_path}")
        return

    with open(templates_config_path, 'r', encoding='utf-8') as f:
        config = yaml.safe_load(f)

    templates = config.get('templates', [])
    if not templates:
        if verbose:
            print("Warning: No templates found in templates.yaml")
        return

    # Load variables configuration
    variables_map = {}
    if variables_config_path.exists():
        with open(variables_config_path, 'r', encoding='utf-8') as f:
            variables_config = yaml.safe_load(f)
            for var_entry in variables_config.get('variables', []):
                variables_map[var_entry['function_tag']] = var_entry['variables']

    with engine.connect() as conn:
        seeded_count = 0
        skipped_count = 0
        meta_seeded_count = 0
        meta_skipped_count = 0

        for template_config in templates:
            function_tag = template_config['function_tag']
            version = template_config['version']
            title = template_config['title']
            template_type = template_config.get('template_type')
            is_active = template_config.get('is_active', True)
            content_file = template_config['content_file']

            # Check if template already exists
            result = conn.execute(
                text("""
                    SELECT COUNT(*) FROM prompt_templates
                    WHERE function_tag = :tag AND version = :ver
                """),
                {"tag": function_tag, "ver": version}
            )
            exists = result.scalar() > 0

            if exists:
                if verbose:
                    print(f"  Template {function_tag} v{version} already exists, skipping")
                skipped_count += 1
                continue

            # Load template content from file
            content_path = templates_dir / content_file
            if not content_path.exists():
                if verbose:
                    print(f"  Warning: Template file not found: {content_path}")
                continue

            with open(content_path, 'r', encoding='utf-8') as f:
                template_content = f.read()

            # Insert template
            conn.execute(
                text("""
                    INSERT INTO prompt_templates
                    (function_tag, version, title, template_content, template_type, is_active, created_at, updated_at)
                    VALUES (:tag, :ver, :title, :content, :type, :active, NOW(), NOW())
                """),
                {
                    "tag": function_tag,
                    "ver": version,
                    "title": title,
                    "content": template_content,
                    "type": template_type,
                    "active": is_active
                }
            )
            seeded_count += 1

            if verbose:
                print(f"  Seeded: {function_tag} v{version} - {title}")

        # Seed prompt_meta (variable definitions)
        if variables_map:
            if verbose:
                print("\n  Seeding variable definitions (prompt_meta)...")

            for function_tag, variables in variables_map.items():
                # Check if meta already exists
                result = conn.execute(
                    text("SELECT COUNT(*) FROM prompt_meta WHERE function_tag = :tag"),
                    {"tag": function_tag}
                )
                meta_exists = result.scalar() > 0

                if meta_exists:
                    if verbose:
                        print(f"    Variables for {function_tag} already exist, skipping")
                    meta_skipped_count += 1
                    continue

                # Insert prompt_meta
                import json
                conn.execute(
                    text("""
                        INSERT INTO prompt_meta (function_tag, variables, created_at, updated_at)
                        VALUES (:tag, CAST(:vars AS jsonb), NOW(), NOW())
                    """),
                    {
                        "tag": function_tag,
                        "vars": json.dumps(variables)
                    }
                )
                meta_seeded_count += 1

                if verbose:
                    print(f"    Seeded variables for: {function_tag} ({len(variables)} variables)")

        conn.commit()

        if verbose:
            print(f"\nTemplate seeding complete: {seeded_count} seeded, {skipped_count} skipped")
            if variables_map:
                print(f"Variable definitions: {meta_seeded_count} seeded, {meta_skipped_count} skipped")


def seed_simple_conversion_templates(verbose: bool = False) -> None:
    """
    DEPRECATED: Use seed_prompt_templates() instead.

    This function is kept for backwards compatibility but now just calls
    the new file-based seeding function.
    """
    if verbose:
        print("Note: seed_simple_conversion_templates() is deprecated, using seed_prompt_templates()")
    seed_prompt_templates(verbose=verbose)


def create_experiments_triggers(verbose: bool = False) -> None:
    """
    Create triggers for experiments table.

    Creates trigger to auto-update the updated_at timestamp.

    Args:
        verbose: If True, print progress information.
    """
    if verbose:
        print("Creating experiments triggers...")

    with engine.connect() as conn:
        # Create trigger function for updated_at
        conn.execute(text("""
            CREATE OR REPLACE FUNCTION update_experiments_updated_at()
            RETURNS TRIGGER AS $$
            BEGIN
                NEW.updated_at = CURRENT_TIMESTAMP;
                RETURN NEW;
            END;
            $$ LANGUAGE plpgsql
        """))

        # Create trigger
        conn.execute(text("DROP TRIGGER IF EXISTS trigger_update_experiments_updated_at ON experiments"))
        conn.execute(text("""
            CREATE TRIGGER trigger_update_experiments_updated_at
                BEFORE UPDATE ON experiments
                FOR EACH ROW
                EXECUTE FUNCTION update_experiments_updated_at()
        """))

        conn.commit()

    # Transfer ownership to app user
    db_config = load_config().database
    app_user = db_config.app_user

    try:
        with engine.connect() as conn:
            conn.execute(text(f'ALTER FUNCTION update_experiments_updated_at() OWNER TO "{app_user}"'))
            conn.commit()
            if verbose:
                print(f"Transferred ownership of experiments trigger function to {app_user}")
    except Exception as e:
        if verbose:
            print(f"Note: Could not transfer ownership (this is okay if running as app user): {e}")

    if verbose:
        print("Experiments triggers created successfully")


def create_default_rag_config(verbose: bool = False) -> None:
    """
    Create rag_config table and default preset if none exists.

    This function is idempotent - it creates the table if needed and only
    inserts the default preset if the table is empty.

    Args:
        verbose: If True, print progress information.
    """
    if verbose:
        print("Creating RAG config table and default preset...")

    with engine.connect() as conn:
        # Create rag_config table
        conn.execute(text("""
            CREATE TABLE IF NOT EXISTS rag_config (
                id SERIAL PRIMARY KEY,
                preset_name VARCHAR(100) UNIQUE NOT NULL,
                is_default BOOLEAN NOT NULL DEFAULT FALSE,
                description TEXT,
                config JSONB NOT NULL,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """))

        # Create indexes
        conn.execute(text("""
            CREATE INDEX IF NOT EXISTS idx_rag_config_preset_name ON rag_config(preset_name)
        """))
        conn.execute(text("""
            CREATE INDEX IF NOT EXISTS idx_rag_config_is_default ON rag_config(is_default) WHERE is_default = TRUE
        """))

        # Create trigger function for updated_at
        conn.execute(text("""
            CREATE OR REPLACE FUNCTION update_rag_config_updated_at()
            RETURNS TRIGGER AS $$
            BEGIN
                NEW.updated_at = CURRENT_TIMESTAMP;
                RETURN NEW;
            END;
            $$ LANGUAGE plpgsql
        """))

        # Create trigger for updated_at
        conn.execute(text("DROP TRIGGER IF EXISTS trigger_update_rag_config_updated_at ON rag_config"))
        conn.execute(text("""
            CREATE TRIGGER trigger_update_rag_config_updated_at
                BEFORE UPDATE ON rag_config
                FOR EACH ROW
                EXECUTE FUNCTION update_rag_config_updated_at()
        """))

        # Create trigger function to enforce single default
        conn.execute(text("""
            CREATE OR REPLACE FUNCTION ensure_single_default_rag_config()
            RETURNS TRIGGER AS $$
            BEGIN
                IF NEW.is_default = TRUE THEN
                    UPDATE rag_config SET is_default = FALSE WHERE id != NEW.id;
                END IF;
                RETURN NEW;
            END;
            $$ LANGUAGE plpgsql
        """))

        # Create trigger to enforce single default
        conn.execute(text("DROP TRIGGER IF EXISTS trigger_ensure_single_default_rag_config ON rag_config"))
        conn.execute(text("""
            CREATE TRIGGER trigger_ensure_single_default_rag_config
                AFTER INSERT OR UPDATE ON rag_config
                FOR EACH ROW
                WHEN (NEW.is_default = TRUE)
                EXECUTE FUNCTION ensure_single_default_rag_config()
        """))

        # Check if any presets exist
        result = conn.execute(text("SELECT COUNT(*) FROM rag_config"))
        count = result.scalar()

        if count > 0:
            if verbose:
                print("RAG config presets already exist, skipping default creation")
        else:
            # Insert default preset with balanced settings
            conn.execute(text("""
                INSERT INTO rag_config (preset_name, is_default, description, config)
                VALUES (
                    'Default',
                    TRUE,
                    'Default RAG configuration with balanced settings for general-purpose queries',
                    :config
                )
            """), {"config": """{
                "retrieval": {
                    "dense_limit": 19,
                    "lexical_limit": 5,
                    "rrf_k": 50,
                    "top_k_rrf": 75,
                    "top_n_final": 17,
                    "entity_boost": 0.05,
                    "min_word_count": 150,
                    "max_word_count": 750,
                    "mmr_lambda": 0.7,
                    "reranker_batch_size": 8,
                    "reranker_max_length": 512,
                    "min_sentence_filter_enabled": false,
                    "min_sentence_count": 5
                },
                "consolidation": {
                    "coverage_threshold": 0.5,
                    "line_gap": 7,
                    "min_content_length": 350
                },
                "augmentation": {
                    "top_n_contexts": 5
                }
            }"""})

            if verbose:
                print("Default RAG config preset created successfully")

        conn.commit()

    # Transfer ownership to app user to ensure proper permissions
    # This is necessary if init_db was run with admin credentials
    db_config = load_config().database
    app_user = db_config.app_user

    try:
        with engine.connect() as conn:
            # Transfer function ownership
            conn.execute(text(f'ALTER FUNCTION update_rag_config_updated_at() OWNER TO "{app_user}"'))
            conn.execute(text(f'ALTER FUNCTION ensure_single_default_rag_config() OWNER TO "{app_user}"'))

            # Transfer sequence ownership
            conn.execute(text(f'ALTER SEQUENCE IF EXISTS rag_config_id_seq OWNER TO "{app_user}"'))

            conn.commit()

            if verbose:
                print(f"Transferred ownership of RAG config objects to {app_user}")
    except Exception as e:
        # If we can't transfer ownership (e.g., not running as admin), that's okay
        # as long as the app user has usage permissions
        if verbose:
            print(f"Note: Could not transfer ownership (this is okay if running as app user): {e}")

    if verbose:
        print("RAG config table and preset setup complete")


def create_result_models_table(verbose: bool = False) -> None:
    """
    Create result_models table for tracking LLM models used to generate results.

    This function is idempotent - it creates the table if needed and sets up
    the trigger for auto-updating the updated_at timestamp.

    Args:
        verbose: If True, print progress information.
    """
    if verbose:
        print("Creating result_models table...")

    with engine.connect() as conn:
        # Create result_models table
        conn.execute(text("""
            CREATE TABLE IF NOT EXISTS result_models (
                id SERIAL PRIMARY KEY,
                name VARCHAR(200) UNIQUE NOT NULL,
                created_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT NOW(),
                updated_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT NOW()
            )
        """))

        # Create index on name for unique constraint lookups
        conn.execute(text("""
            CREATE INDEX IF NOT EXISTS ix_result_models_name ON result_models(name)
        """))

        # Create trigger function for auto-updating updated_at timestamp
        conn.execute(text("""
            CREATE OR REPLACE FUNCTION update_result_models_updated_at()
            RETURNS TRIGGER AS $$
            BEGIN
                NEW.updated_at = NOW();
                RETURN NEW;
            END;
            $$ LANGUAGE plpgsql
        """))

        # Create trigger
        conn.execute(text("DROP TRIGGER IF EXISTS trigger_update_result_models_updated_at ON result_models"))
        conn.execute(text("""
            CREATE TRIGGER trigger_update_result_models_updated_at
                BEFORE UPDATE ON result_models
                FOR EACH ROW
                EXECUTE FUNCTION update_result_models_updated_at()
        """))

        # Add model_id column to results table if not exists
        conn.execute(text("""
            DO $$ BEGIN
                ALTER TABLE results
                ADD COLUMN IF NOT EXISTS model_id INTEGER NULL
                REFERENCES result_models(id) ON DELETE SET NULL;
            EXCEPTION
                WHEN duplicate_column THEN NULL;
            END $$;
        """))

        # Create index on model_id for join performance
        conn.execute(text("""
            CREATE INDEX IF NOT EXISTS ix_results_model_id ON results(model_id)
        """))

        conn.commit()

    # Transfer ownership to app user
    db_config = load_config().database
    app_user = db_config.app_user

    try:
        with engine.connect() as conn:
            conn.execute(text(f'ALTER FUNCTION update_result_models_updated_at() OWNER TO "{app_user}"'))
            conn.execute(text(f'ALTER SEQUENCE IF EXISTS result_models_id_seq OWNER TO "{app_user}"'))
            conn.commit()
            if verbose:
                print(f"Transferred ownership of result_models objects to {app_user}")
    except Exception as e:
        if verbose:
            print(f"Note: Could not transfer ownership (this is okay if running as app user): {e}")

    if verbose:
        print("result_models table created successfully")


def seed_default_result_model(verbose: bool = False) -> None:
    """
    Seed default "Unspecified" model record in result_models table.

    This function is idempotent - it only inserts the default model if it
    doesn't already exist.

    Args:
        verbose: If True, print progress information.
    """
    if verbose:
        print("Seeding default result model...")

    with engine.connect() as conn:
        # Seed default "Unspecified" model
        conn.execute(text("""
            INSERT INTO result_models (name, created_at, updated_at)
            VALUES ('Unspecified', NOW(), NOW())
            ON CONFLICT (name) DO NOTHING
        """))
        conn.commit()

        if verbose:
            print("Default 'Unspecified' result model seeded")


def init_database(verbose: bool = False) -> None:
    """
    Initialize the database: create database, user, tables, and indexes.

    Args:
        verbose: If True, print progress information.
    """
    create_database_and_user(verbose=verbose)
    enable_pgvector_extension(verbose=verbose)
    create_enums(verbose=verbose)
    create_tables(verbose=verbose)
    create_io_files_triggers(verbose=verbose)
    create_experiments_triggers(verbose=verbose)
    create_vector_indexes(verbose=verbose)
    create_fulltext_search(verbose=verbose)
    create_history_indexes(verbose=verbose)
    create_prompt_meta_table(verbose=verbose)
    create_result_models_table(verbose=verbose)
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
