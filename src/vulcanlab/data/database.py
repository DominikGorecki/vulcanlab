"""
Database connection and session management.

Database configuration (host, port, users) loaded from vulcanlab.config.json.
Passwords (secrets) loaded from .env file.
"""

import os
from contextlib import contextmanager
from typing import Generator

from dotenv import load_dotenv
from sqlalchemy import create_engine
from sqlalchemy.orm import Session, sessionmaker, declarative_base

from vulcanlab.config import load_config
from vulcanlab.data.env_utils import get_required_env_var

# Load environment variables for passwords
load_dotenv()


def get_database_url(force_reload: bool = False) -> str:
    """Get database connection URL from configuration.
    
    Args:
        force_reload: Whether to reload configuration from file
        
    Returns:
        PostgreSQL connection string
    """
    db_config = load_config(force_reload=force_reload).database
    
    # Passwords from .env (secrets)
    # Note: os.getenv doesn't update if .env file changes unless load_dotenv is called again
    if force_reload:
        load_dotenv(override=True)

    app_pwd = get_required_env_var("POSTGRES_APP_PASSWORD", "Application database password")
    
    return (
        f"postgresql+psycopg://{db_config.app_user}:{app_pwd}"
        f"@{db_config.host}:{db_config.port}/{db_config.db_name}"
    )


# Initial load of configuration
_db_config = load_config().database

# Database configuration from JSON (kept for backward compatibility)
POSTGRES_HOST = _db_config.host
POSTGRES_PORT = _db_config.port
POSTGRES_DB = _db_config.db_name
POSTGRES_APP_USER = _db_config.app_user
POSTGRES_ADMIN_USER = _db_config.admin_user

# Passwords from .env (secrets)
POSTGRES_APP_PASSWORD = get_required_env_var("POSTGRES_APP_PASSWORD", "Application database password")
POSTGRES_ADMIN_PASSWORD = get_required_env_var("POSTGRES_ADMIN_PASSWORD", "Admin database password")

# Build database URL
DATABASE_URL = get_database_url()

# Create engine with psycopg3 workaround
# The prepare_threshold parameter disables prepared statements which avoids
# the bytes/string version detection bug in psycopg3
engine = create_engine(
    DATABASE_URL,
    echo=False,
    connect_args={"prepare_threshold": None}
)

# Create session factory
SessionLocal = sessionmaker(bind=engine, autocommit=False, autoflush=False)

# Base class for declarative models
Base = declarative_base()


@contextmanager
def get_session() -> Generator[Session, None, None]:
    """
    Provide a transactional scope around a series of operations.

    Usage:
        with get_session() as session:
            session.add(some_object)
            session.commit()

    Yields:
        SQLAlchemy Session object.
    """
    session = SessionLocal()
    try:
        yield session
    except Exception:
        session.rollback()
        raise
    finally:
        session.close()


def get_db_session() -> Generator[Session, None, None]:
    """
    FastAPI dependency for database sessions.

    This is a plain generator function (not a context manager) that works
    with FastAPI's Depends() system.

    Usage:
        @app.get("/items")
        def get_items(session: Session = Depends(get_db_session)):
            return session.query(Item).all()

    Yields:
        SQLAlchemy Session object.
    """
    session = SessionLocal()
    try:
        yield session
    except Exception:
        session.rollback()
        raise
    finally:
        session.close()


def get_admin_database_url() -> str:
    """
    Get database URL using admin credentials.

    Reads configuration dynamically to support testing with patched environment variables.
    Environment variables take precedence over config file values.

    Returns:
        PostgreSQL connection URL for admin user.
    """
    # Read config dynamically to support testing
    db_config = load_config().database
    # Check environment variables first (for testing), then fall back to config
    admin_user = os.getenv("POSTGRES_ADMIN_USER", db_config.admin_user)
    admin_password = get_required_env_var("POSTGRES_ADMIN_PASSWORD", "Admin database password")
    host = os.getenv("POSTGRES_HOST", db_config.host)
    port = os.getenv("POSTGRES_PORT", str(db_config.port))
    
    return (
        f"postgresql+psycopg://{admin_user}:{admin_password}"
        f"@{host}:{port}/postgres"
    )
