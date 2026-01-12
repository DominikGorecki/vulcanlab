"""
Database and user creation functions.

Handles initial PostgreSQL setup including database creation,
user creation, privilege grants, and extension enablement.
"""

from dotenv import load_dotenv
from sqlalchemy import create_engine, text

from vulcanlab.config import load_config
from .database import get_admin_database_url
from .env_utils import get_required_env_var


def create_database_and_user(verbose: bool = False) -> None:
    """
    Create the database and application user if they don't exist.

    Creates the PostgreSQL database and application user based on
    configuration from vulcanlab.config.json, with passwords from
    environment variables.

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

    Requires admin privileges to create extensions.

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
