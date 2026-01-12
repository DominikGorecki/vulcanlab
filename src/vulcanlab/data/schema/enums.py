"""
PostgreSQL enum type creation.

Creates custom enum types required by the database models.
"""

from sqlalchemy import text

from ..database import engine


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

        # Create collection_item_type enum
        conn.execute(text("""
            DO $$ BEGIN
                CREATE TYPE collection_item_type AS ENUM ('excerpt', 'research_result', 'research_query');
            EXCEPTION
                WHEN duplicate_object THEN NULL;
            END $$;
        """))

        conn.commit()

    if verbose:
        print("Enum types created successfully")
