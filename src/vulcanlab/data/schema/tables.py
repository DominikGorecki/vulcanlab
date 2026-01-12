"""
SQLAlchemy ORM table creation.

Creates all tables defined in the models using SQLAlchemy's metadata.
"""

from ..database import Base, engine


def create_tables(verbose: bool = False) -> None:
    """
    Create all tables defined in the models.

    Uses SQLAlchemy's Base.metadata.create_all() to create tables
    from registered ORM models.

    Args:
        verbose: If True, print progress information.
    """
    if verbose:
        print("Creating tables...")

    Base.metadata.create_all(bind=engine)

    if verbose:
        print("Tables created successfully")
