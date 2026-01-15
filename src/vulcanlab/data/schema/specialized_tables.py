"""
Specialized table creation for feature-specific database objects.

Contains functions for creating tables that require custom triggers,
indexes, or initialization logic beyond what SQLAlchemy ORM provides.
"""

from sqlalchemy import text

from vulcanlab.config import load_config
from ..database import engine
from .triggers import transfer_function_ownership


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
    transfer_function_ownership(
        function_names=["update_prompt_meta_updated_at"],
        sequence_names=["prompt_meta_id_seq"],
        verbose=verbose
    )

    if verbose:
        print("prompt_meta table created successfully")


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
    transfer_function_ownership(
        function_names=["update_result_models_updated_at"],
        sequence_names=["result_models_id_seq"],
        verbose=verbose
    )

    if verbose:
        print("result_models table created successfully")


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

    # Transfer ownership to app user
    transfer_function_ownership(
        function_names=["update_rag_config_updated_at", "ensure_single_default_rag_config"],
        sequence_names=["rag_config_id_seq"],
        verbose=verbose
    )

    if verbose:
        print("RAG config table and preset setup complete")


def create_collections_table(verbose: bool = False) -> None:
    """
    Create collections and collection_items tables with triggers and indexes.

    The tables themselves are created by SQLAlchemy create_all(), but we need
    manual indexes and triggers matching migration 027.

    Args:
        verbose: If True, print progress information.
    """
    if verbose:
        print("Creating collections and collection_items tables...")

    with engine.connect() as conn:
        # Create GIN index on collections.tags
        conn.execute(text("""
            CREATE INDEX IF NOT EXISTS idx_collections_tags
            ON collections USING GIN (tags)
        """))

        # Create trigger function for collections.updated_at
        conn.execute(text("""
            CREATE OR REPLACE FUNCTION update_collections_updated_at()
            RETURNS TRIGGER AS $$
            BEGIN
                NEW.updated_at = NOW();
                RETURN NEW;
            END;
            $$ LANGUAGE plpgsql
        """))

        # Create trigger for collections.updated_at
        conn.execute(text("DROP TRIGGER IF EXISTS trigger_update_collections_updated_at ON collections"))
        conn.execute(text("""
            CREATE TRIGGER trigger_update_collections_updated_at
                BEFORE UPDATE ON collections
                FOR EACH ROW
                EXECUTE FUNCTION update_collections_updated_at()
        """))

        # Create trigger function for collection_items.last_modified
        conn.execute(text("""
            CREATE OR REPLACE FUNCTION update_collection_items_last_modified()
            RETURNS TRIGGER AS $$
            BEGIN
                NEW.last_modified = NOW();
                RETURN NEW;
            END;
            $$ LANGUAGE plpgsql
        """))

        # Create trigger for collection_items.last_modified
        conn.execute(text("DROP TRIGGER IF EXISTS trigger_update_collection_items_last_modified ON collection_items"))
        conn.execute(text("""
            CREATE TRIGGER trigger_update_collection_items_last_modified
                BEFORE UPDATE ON collection_items
                FOR EACH ROW
                EXECUTE FUNCTION update_collection_items_last_modified()
        """))

        conn.commit()

    # Transfer ownership to app user
    transfer_function_ownership(
        function_names=["update_collections_updated_at", "update_collection_items_last_modified"],
        verbose=verbose
    )

    if verbose:
        print("Collections and collection_items infrastructure created successfully")


def create_research_tables(verbose: bool = False) -> None:
    """
    Create research_sessions, research_sections, and research_reports tables.

    These tables support the deep research feature with JSONB-based state storage
    for manual and automated research workflows.

    Args:
        verbose: If True, print progress information.
    """
    if verbose:
        print("Creating research tables...")

    with engine.connect() as conn:
        # Create research_sessions table
        conn.execute(text("""
            CREATE TABLE IF NOT EXISTS research_sessions (
                id SERIAL PRIMARY KEY,
                collection_id INTEGER NOT NULL REFERENCES collections(id) ON DELETE CASCADE,
                session_type VARCHAR(20) NOT NULL,
                thread_id VARCHAR(255) UNIQUE NOT NULL,
                current_phase VARCHAR(50),
                research_plan JSONB,
                state_data JSONB,
                status VARCHAR(20) NOT NULL DEFAULT 'in_progress',
                created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP NOT NULL,
                updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP NOT NULL,
                completed_at TIMESTAMP WITH TIME ZONE,
                CONSTRAINT chk_research_sessions_session_type CHECK (session_type IN ('manual', 'automated')),
                CONSTRAINT chk_research_sessions_status CHECK (status IN ('in_progress', 'completed', 'failed', 'paused'))
            )
        """))

        # Create research_sections table
        conn.execute(text("""
            CREATE TABLE IF NOT EXISTS research_sections (
                id SERIAL PRIMARY KEY,
                session_id INTEGER NOT NULL REFERENCES research_sessions(id) ON DELETE CASCADE,
                question_id VARCHAR(50),
                question_text TEXT,
                section_content TEXT,
                context_data JSONB,
                matching_results JSONB,
                metadata JSONB,
                reuse_info JSONB,
                quality_status VARCHAR(20),
                created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP NOT NULL,
                updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP NOT NULL,
                CONSTRAINT chk_research_sections_quality_status CHECK (
                    quality_status IS NULL OR quality_status IN ('pending', 'pass', 'fail', 'needs_review')
                )
            )
        """))

        # Create research_reports table
        conn.execute(text("""
            CREATE TABLE IF NOT EXISTS research_reports (
                id SERIAL PRIMARY KEY,
                session_id INTEGER NOT NULL REFERENCES research_sessions(id) ON DELETE CASCADE,
                report_content TEXT NOT NULL,
                executive_summary TEXT,
                quality_evaluation JSONB,
                metadata JSONB,
                version INTEGER NOT NULL DEFAULT 1,
                created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP NOT NULL
            )
        """))

        # Create indexes for research_sessions
        conn.execute(text("""
            CREATE INDEX IF NOT EXISTS idx_research_sessions_collection ON research_sessions(collection_id)
        """))
        conn.execute(text("""
            CREATE INDEX IF NOT EXISTS idx_research_sessions_thread ON research_sessions(thread_id)
        """))
        conn.execute(text("""
            CREATE INDEX IF NOT EXISTS idx_research_sessions_status ON research_sessions(status)
        """))

        # Create indexes for research_sections
        conn.execute(text("""
            CREATE INDEX IF NOT EXISTS idx_research_sections_session ON research_sections(session_id)
        """))
        conn.execute(text("""
            CREATE INDEX IF NOT EXISTS idx_research_sections_question ON research_sections(question_id)
        """))
        conn.execute(text("""
            CREATE INDEX IF NOT EXISTS idx_research_sections_quality ON research_sections(quality_status)
        """))

        # Create index for research_reports
        conn.execute(text("""
            CREATE INDEX IF NOT EXISTS idx_research_reports_session ON research_reports(session_id)
        """))

        # Create trigger function for research_sessions.updated_at
        conn.execute(text("""
            CREATE OR REPLACE FUNCTION update_research_sessions_updated_at()
            RETURNS TRIGGER AS $$
            BEGIN
                NEW.updated_at = CURRENT_TIMESTAMP;
                RETURN NEW;
            END;
            $$ LANGUAGE plpgsql
        """))

        # Create trigger for research_sessions.updated_at
        conn.execute(text("DROP TRIGGER IF EXISTS trigger_update_research_sessions_updated_at ON research_sessions"))
        conn.execute(text("""
            CREATE TRIGGER trigger_update_research_sessions_updated_at
                BEFORE UPDATE ON research_sessions
                FOR EACH ROW
                EXECUTE FUNCTION update_research_sessions_updated_at()
        """))

        # Create trigger function for research_sections.updated_at
        conn.execute(text("""
            CREATE OR REPLACE FUNCTION update_research_sections_updated_at()
            RETURNS TRIGGER AS $$
            BEGIN
                NEW.updated_at = CURRENT_TIMESTAMP;
                RETURN NEW;
            END;
            $$ LANGUAGE plpgsql
        """))

        # Create trigger for research_sections.updated_at
        conn.execute(text("DROP TRIGGER IF EXISTS trigger_update_research_sections_updated_at ON research_sections"))
        conn.execute(text("""
            CREATE TRIGGER trigger_update_research_sections_updated_at
                BEFORE UPDATE ON research_sections
                FOR EACH ROW
                EXECUTE FUNCTION update_research_sections_updated_at()
        """))

        conn.commit()

    # Transfer ownership to app user
    transfer_function_ownership(
        function_names=["update_research_sessions_updated_at", "update_research_sections_updated_at"],
        sequence_names=["research_sessions_id_seq", "research_sections_id_seq", "research_reports_id_seq"],
        verbose=verbose
    )

    if verbose:
        print("Research tables created successfully")


def create_summary_tables(verbose: bool = False) -> None:
    """
    Create summary_nodes, work_summaries, and summarize_settings tables.

    Implementation of Ticket: work-summarization.T03

    Args:
        verbose: If True, print progress information.
    """
    if verbose:
        print("Creating summary and settings tables...")

    with engine.connect() as conn:
        # 1. Create summarize_settings table
        conn.execute(text("""
            CREATE TABLE IF NOT EXISTS summarize_settings (
                id SERIAL PRIMARY KEY,
                h1_always_summarize BOOLEAN DEFAULT true,
                h2_top_percent INTEGER DEFAULT 100,
                h3_salience_threshold FLOAT DEFAULT 0.5,
                h4_salience_threshold FLOAT DEFAULT 0.7,
                definition_density_weight FLOAT DEFAULT 0.3,
                list_density_weight FLOAT DEFAULT 0.2,
                keyphrase_novelty_weight FLOAT DEFAULT 0.2,
                location_prior_weight FLOAT DEFAULT 0.15,
                heading_depth_weight FLOAT DEFAULT 0.15,
                created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP NOT NULL,
                updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP NOT NULL
            )
        """))

        # 2. Create summary_nodes table
        conn.execute(text("""
            CREATE TABLE IF NOT EXISTS summary_nodes (
                id SERIAL PRIMARY KEY,
                chunk_id INTEGER NOT NULL REFERENCES chunks(id) ON DELETE CASCADE,
                work_id INTEGER NOT NULL REFERENCES works(id) ON DELETE CASCADE,
                gist TEXT NOT NULL,
                key_points JSONB NOT NULL DEFAULT '[]',
                definitions JSONB NOT NULL DEFAULT '[]',
                key_terms JSONB NOT NULL DEFAULT '[]',
                examples JSONB NOT NULL DEFAULT '[]',
                start_line INTEGER NOT NULL,
                end_line INTEGER NOT NULL,
                salience_score FLOAT NOT NULL,
                created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP NOT NULL
            )
        """))

        # 3. Create work_summaries table
        conn.execute(text("""
            CREATE TABLE IF NOT EXISTS work_summaries (
                id SERIAL PRIMARY KEY,
                work_id INTEGER NOT NULL REFERENCES works(id) ON DELETE CASCADE,
                type VARCHAR(30) NOT NULL,
                content JSONB NOT NULL,
                line_references JSONB NOT NULL,
                created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP NOT NULL,
                CONSTRAINT chk_work_summary_type CHECK (type IN ('abstract', 'outline', 'key_concepts', 'chapter_summaries')),
                CONSTRAINT unq_work_summary_work_type UNIQUE (work_id, type)
            )
        """))

        # Indexes for summary_nodes
        conn.execute(text("CREATE INDEX IF NOT EXISTS idx_summary_nodes_work_id ON summary_nodes(work_id)"))
        conn.execute(text("CREATE INDEX IF NOT EXISTS idx_summary_nodes_chunk_id ON summary_nodes(chunk_id)"))

        # Index for work_summaries
        conn.execute(text("CREATE INDEX IF NOT EXISTS idx_work_summaries_work_id ON work_summaries(work_id)"))

        # Trigger function for summarize_settings.updated_at
        conn.execute(text("""
            CREATE OR REPLACE FUNCTION update_summarize_settings_updated_at()
            RETURNS TRIGGER AS $$
            BEGIN
                NEW.updated_at = CURRENT_TIMESTAMP;
                RETURN NEW;
            END;
            $$ LANGUAGE plpgsql
        """))

        # Trigger for summarize_settings.updated_at
        conn.execute(text("DROP TRIGGER IF EXISTS trigger_update_summarize_settings_updated_at ON summarize_settings"))
        conn.execute(text("""
            CREATE TRIGGER trigger_update_summarize_settings_updated_at
                BEFORE UPDATE ON summarize_settings
                FOR EACH ROW
                EXECUTE FUNCTION update_summarize_settings_updated_at()
        """))

        conn.commit()

    # Transfer ownership to app user
    transfer_function_ownership(
        function_names=["update_summarize_settings_updated_at"],
        sequence_names=["summarize_settings_id_seq", "summary_nodes_id_seq", "work_summaries_id_seq"],
        verbose=verbose
    )

    if verbose:
        print("Summary and settings tables created successfully")
