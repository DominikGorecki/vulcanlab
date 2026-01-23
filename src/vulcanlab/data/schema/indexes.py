"""
Index creation for vector search, full-text search, and query optimization.

Contains functions for creating specialized PostgreSQL indexes including
HNSW indexes for pgvector, GIN indexes for full-text search, and
optimization indexes for common query patterns.
"""

from sqlalchemy import text

from vulcanlab.config import load_config
from ..database import engine
from .triggers import transfer_function_ownership


def create_vector_indexes(verbose: bool = False) -> None:
    """
    Create HNSW indexes for vector columns and other chunk optimization indexes.

    Creates indexes for:
    - chunks.embedding (cosine similarity)
    - queries.embedding_original (cosine similarity)
    - queries.embedding_hyde (cosine similarity)
    - chunks.sentence_count (filtering)
    - chunks.dense_lexical_use (retrieval filtering)

    Args:
        verbose: If True, print progress information.
    """
    if verbose:
        print("Creating vector indexes...")

    with engine.connect() as conn:
        # 1. Ensure retrieval optimization columns exist
        conn.execute(text("""
            ALTER TABLE chunks ADD COLUMN IF NOT EXISTS dense_lexical_use BOOLEAN NOT NULL DEFAULT FALSE
        """))

        # 2. Create HNSW index for cosine similarity on chunks.embedding
        conn.execute(text("""
            CREATE INDEX IF NOT EXISTS ix_chunks_embedding_hnsw
            ON chunks USING hnsw (embedding vector_cosine_ops)
        """))

        # 3. Create HNSW indexes for queries table embeddings
        conn.execute(text("""
            CREATE INDEX IF NOT EXISTS ix_queries_embedding_original_hnsw
            ON queries USING hnsw (embedding_original vector_cosine_ops)
        """))
        conn.execute(text("""
            CREATE INDEX IF NOT EXISTS ix_queries_embedding_hyde_hnsw
            ON queries USING hnsw (embedding_hyde vector_cosine_ops)
        """))

        # 4. Create index on sentence_count for filtering (migration 019)
        conn.execute(text("""
            CREATE INDEX IF NOT EXISTS idx_chunks_sentence_count
            ON chunks (sentence_count)
        """))

        # 5. Create index on dense_lexical_use for filtering (migration 033)
        conn.execute(text("""
            CREATE INDEX IF NOT EXISTS ix_chunks_dense_lexical_use
            ON chunks (dense_lexical_use)
        """))

        conn.commit()

    if verbose:
        print("Vector indexes created successfully")


def create_fulltext_search(verbose: bool = False) -> None:
    """
    Create full-text search infrastructure for chunks.

    This adds:
    - tsvector column for pre-computed search vectors
    - GIN index for efficient full-text queries
    - Trigger to auto-update tsvector on content changes

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
    transfer_function_ownership(
        function_names=["chunks_content_tsvector_trigger"],
        verbose=verbose
    )

    if verbose:
        print("Full-text search infrastructure created successfully")


def ensure_vector_dimensions(target_dim: int = 1536, verbose: bool = False) -> None:
    """
    Ensure vector columns have the correct dimensions, altering if necessary.

    Queries pg_attribute to detect current vector dimensions for each column.
    If a column's dimension doesn't match target_dim, drops the HNSW index
    (which is dimension-specific) and alters the column type.

    Note: Vector type stores dimension in atttypmod as (dim + 4), so:
    - 768 dimensions = atttypmod 772
    - 1536 dimensions = atttypmod 1540

    Args:
        target_dim: Target dimension for vector columns (default 1536).
        verbose: If True, print progress information.

    Raises:
        RuntimeError: If a column cannot be altered (e.g., non-NULL values exist).
    """
    # Define columns to check: (table_name, column_name, hnsw_index_name)
    vector_columns = [
        ("chunks", "embedding", "ix_chunks_embedding_hnsw"),
        ("queries", "embedding_original", "ix_queries_embedding_original_hnsw"),
        ("queries", "embedding_hyde", "ix_queries_embedding_hyde_hnsw"),
    ]

    target_atttypmod = target_dim + 4

    with engine.connect() as conn:
        for table_name, column_name, index_name in vector_columns:
            # Query pg_attribute to get current dimension
            result = conn.execute(text("""
                SELECT a.atttypmod
                FROM pg_attribute a
                JOIN pg_class c ON a.attrelid = c.oid
                JOIN pg_namespace n ON c.relnamespace = n.oid
                WHERE c.relname = :table_name
                  AND a.attname = :column_name
                  AND n.nspname = 'public'
                  AND a.attnum > 0
                  AND NOT a.attisdropped
            """), {"table_name": table_name, "column_name": column_name})

            row = result.fetchone()

            if row is None:
                if verbose:
                    print(f"  Column {table_name}.{column_name} not found, skipping")
                continue

            current_atttypmod = row[0]

            # atttypmod of -1 means no dimension specified (shouldn't happen for vector)
            if current_atttypmod == -1:
                if verbose:
                    print(f"  Column {table_name}.{column_name} has no dimension, skipping")
                continue

            current_dim = current_atttypmod - 4

            if current_dim == target_dim:
                if verbose:
                    print(f"  Column {table_name}.{column_name} already at {target_dim} dimensions")
                continue

            # Dimension mismatch - need to alter
            if verbose:
                print(f"  Altering {table_name}.{column_name} from {current_dim} to {target_dim} dimensions")

            # Drop the HNSW index first (it's dimension-specific)
            conn.execute(text(f"DROP INDEX IF EXISTS {index_name}"))
            if verbose:
                print(f"    Dropped index {index_name}")

            # Alter the column type
            conn.execute(text(
                f"ALTER TABLE {table_name} ALTER COLUMN {column_name} TYPE vector({target_dim})"
            ))
            if verbose:
                print(f"    Altered column to vector({target_dim})")

        conn.commit()

    if verbose:
        print("Vector dimension check complete")


def create_history_indexes(verbose: bool = False) -> None:
    """
    Create indexes for efficient history query operations.

    This creates indexes on the works table:
    1. GIN index on processing_status JSONB for efficient JSON queries
    2. General timestamp index for sorting all works by created_at
    3. Partial index for filtering simple conversion works with timestamp sorting

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
