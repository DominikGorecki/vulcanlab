"""
Default data seeding for database initialization.

Seeds default records that are required for the application to function,
such as the default result model.
"""

from sqlalchemy import text

from ..database import engine


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


def seed_summarize_settings(verbose: bool = False) -> None:
    """
    Seed default row in summarize_settings table if empty.

    Args:
        verbose: If True, print progress information.
    """
    if verbose:
        print("Seeding default summarize settings...")

    with engine.connect() as conn:
        # Check if any settings exist
        result = conn.execute(text("SELECT COUNT(*) FROM summarize_settings"))
        count = result.scalar()

        if count > 0:
            if verbose:
                print("Summarize settings already exist, skipping seeding")
        else:
            # Insert default row
            conn.execute(text("""
                INSERT INTO summarize_settings (
                    min_heading_word_count,
                    max_total_heading_words,
                    dense_top_k,
                    lexical_top_k,
                    rrf_k,
                    rrf_top_k,
                    mmr_lambda,
                    mmr_top_n,
                    max_llm_calls,
                    max_tokens_per_call,
                    tokens_per_word,
                    h1_h2_min_chunks,
                    h3_min_chunks
                )
                VALUES (500, 2500, 7, 7, 60, 7, 0.7, 5, 5, 15000, 0.75, 2, 1)
            """))
            conn.commit()

            if verbose:
                print("Default summarize settings seeded")
