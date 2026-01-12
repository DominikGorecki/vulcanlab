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
