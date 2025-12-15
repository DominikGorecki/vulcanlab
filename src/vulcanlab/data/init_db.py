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

from dotenv import load_dotenv
from sqlalchemy import create_engine, text
from sqlalchemy.exc import ProgrammingError

from vulcanlab.config import load_config
from .database import Base, engine, get_admin_database_url
from .env_utils import get_required_env_var

# Import all models to register them with Base
from .models import Chunk, Query, Result, Work, RagConfig  # noqa: F401
from .models.io_file import IOFile  # noqa: F401
from .models.prompt_template import PromptTemplate  # noqa: F401
from .models.prompt_meta import PromptMeta  # noqa: F401
from .models.parsed_markdown import ParsedMarkdown  # noqa: F401
from .models.sanitized_markdown import SanitizedMarkdown  # noqa: F401
from .models.heading_modifications import HeadingModification  # noqa: F401

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


def create_vector_indexes(verbose: bool = False) -> None:
    """
    Create HNSW indexes for vector columns.

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


def seed_simple_conversion_templates(verbose: bool = False) -> None:
    """
    Seed prompt templates for simple conversion.

    Creates two templates:
    - simple_sanitize_small: Full document sanitization
    - simple_sanitize_large: Condensed document analysis
    """
    if verbose:
        print("Seeding simple conversion prompt templates...")

    with engine.connect() as conn:
        # Check if templates already exist
        result = conn.execute(text("""
            SELECT COUNT(*) FROM prompt_templates
            WHERE function_tag IN ('simple_sanitize_small', 'simple_sanitize_large')
        """))
        count = result.scalar()

        if count > 0:
            if verbose:
                print("Simple conversion templates already exist, skipping")
            return

        # Insert simple_sanitize_small template
        conn.execute(text("""
            INSERT INTO prompt_templates (function_tag, version, title, template_content, is_active, created_at, updated_at)
            VALUES (
                'simple_sanitize_small',
                1,
                'Simple Conversion - Small Document Sanitization',
                'You are an expert document processor preparing academic and research documents for a Retrieval-Augmented Generation (RAG) system.

Your task is to process the provided markdown document to ensure it has:
1. **Proper document hierarchy**: Adjust title heading levels to create appropriate nesting based on context.
2. **Clean, RAG-relevant content**: Remove all non-topical content and fix conversion artifacts.

## Instructions

### Hierarchy Adjustments
- Review all headings (lines starting with #, ##, ###, etc.)
- If a heading is NOT actually a title (e.g., page numbers, "References", "Table of Contents"), REMOVE the heading markers (delete the #''s entirely)
- For actual titles, adjust heading levels (H1-H6) to create proper nesting based on semantic relationships
- Ensure logical hierarchy: child sections should be one level deeper than their parent

### Content Sanitization
- **Fix conversion artifacts**: Replace poorly converted symbols/glyphs with correct text using surrounding context
- **Remove meta-information**: Delete download sources, file metadata, copyright notices
- **Remove non-topical sections**: Delete References, Acknowledgments, Table of Contents, page numbers, headers/footers
- **Remove gibberish**: Delete any garbled text that resulted from poor OCR or conversion
- **Preserve RAG-relevant content**: Keep all substantive text related to the document''s main topics

### Output Format
- Return ONLY the sanitized markdown
- Do NOT add explanations, comments, or metadata
- Do NOT wrap output in code blocks or additional formatting
- Maintain markdown syntax (headings with #, lists, emphasis, etc.)

---

## Document to Process

{markdown}

---

## Sanitized Output',
                TRUE,
                NOW(),
                NOW()
            )
        """))

        # Insert simple_sanitize_large template
        conn.execute(text("""
            INSERT INTO prompt_templates (function_tag, version, title, template_content, is_active, created_at, updated_at)
            VALUES (
                'simple_sanitize_large',
                1,
                'Simple Conversion - Large Document Analysis',
                'You are an expert document processor analyzing a large document''s structure for a RAG system.

You will receive a CONDENSED representation showing each heading with contextual sentences. Your task is to provide heading-level modifications.

## Instructions

For each heading, determine:

1. **Action**: Choose one:
   - `KEEP`: Heading is valid, keep as-is
   - `CHANGE`: Heading should be modified (level change, text cleanup)
   - `REMOVE`: Not a real heading (e.g., page numbers, "References")

2. **Modified Heading**: If action=CHANGE, provide the corrected heading with proper markdown level markers (#, ##, ###)
   - Adjust heading level for proper hierarchy
   - Clean up formatting issues (extra spaces, weird characters)
   - If action=REMOVE or action=KEEP, leave this blank

3. **Vectorize**: Choose one:
   - `VECTORIZE`: This section contains RAG-relevant content and should be indexed
   - `SKIP`: This section is not relevant (meta-information, acknowledgments, etc.)

## Output Format

Provide your modifications as a structured list, one per heading:

```
LINE: {line_number}
ACTION: {KEEP|CHANGE|REMOVE}
MODIFIED: {new heading if ACTION=CHANGE, otherwise blank}
VECTORIZE: {VECTORIZE|SKIP}
---
```

## Example

Input:
```
5: ## Introduction
  This paper presents a novel approach to machine learning. We focus on neural networks.
  ...
  The rest of the paper is organized as follows.

12: ### Page 3
  Lorem ipsum dolor sit amet.
```

Output:
```
LINE: 5
ACTION: KEEP
MODIFIED:
VECTORIZE: VECTORIZE
---
LINE: 12
ACTION: REMOVE
MODIFIED:
VECTORIZE: SKIP
---
```

---

## Condensed Document

{condensed_document}

---

## Your Modifications',
                TRUE,
                NOW(),
                NOW()
            )
        """))

        conn.commit()

        if verbose:
            print("Simple conversion templates seeded successfully")


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
                    "min_char_count": 250,
                    "min_content_length": 750,
                    "enrich_lines_above": 0,
                    "enrich_lines_below": 13,
                    "mmr_lambda": 0.7,
                    "reranker_batch_size": 8,
                    "reranker_max_length": 512
                },
                "consolidation": {
                    "coverage_threshold": 0.5,
                    "line_gap": 7,
                    "min_content_length": 350,
                    "enrich_from_md": true
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


def init_database(verbose: bool = False) -> None:
    """
    Initialize the database: create database, user, tables, and indexes.

    Args:
        verbose: If True, print progress information.
    """
    create_database_and_user(verbose=verbose)
    enable_pgvector_extension(verbose=verbose)
    create_tables(verbose=verbose)
    create_vector_indexes(verbose=verbose)
    create_fulltext_search(verbose=verbose)
    create_prompt_meta_table(verbose=verbose)
    seed_prompt_templates(verbose=verbose)
    seed_simple_conversion_templates(verbose=verbose)
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
