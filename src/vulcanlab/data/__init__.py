"""Data models, database connection, and schemas."""

from .database import Base, engine, SessionLocal, get_session
from .models import Work

__all__ = [
    "Base",
    "engine",
    "SessionLocal",
    "get_session",
    "Work",
]


def init_database():
    """Import and run init_database from init_db module."""
    from .init_db import init_database as _init_database
    return _init_database()
