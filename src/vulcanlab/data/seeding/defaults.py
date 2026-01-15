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
    Seed default summarize_settings configuration.

    This function is idempotent - it only inserts the default row if the table is empty.

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
                print("Summarize settings already exist, skipping default creation")
        else:
            # Insert default row
            conn.execute(text("""
                INSERT INTO summarize_settings (
                    h1_always_summarize,
                    h2_top_percent,
                    h3_salience_threshold,
                    h4_salience_threshold,
                    definition_density_weight,
                    list_density_weight,
                    keyphrase_novelty_weight,
                    location_prior_weight,
                    heading_depth_weight
                )
                VALUES (true, 100, 0.5, 0.7, 0.3, 0.2, 0.2, 0.15, 0.15)
            """))
            conn.commit()

            if verbose:
                print("Default summarize settings seeded successfully")
