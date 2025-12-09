"""Database health check module.

This module provides functions to verify database connectivity, schema integrity,
and proper configuration of tables, indexes, triggers, and extensions.
"""

from dataclasses import dataclass
from typing import Optional
import signal
from contextlib import contextmanager

from sqlalchemy import text, inspect, create_engine
from sqlalchemy.exc import SQLAlchemyError

from .database import DATABASE_URL, get_database_url


# Timeout for database operations (in seconds)
DB_TIMEOUT = 5


class TimeoutError(Exception):
    """Raised when a database operation times out."""
    pass


def timeout_handler(signum, frame):
    """Handler for timeout signal."""
    raise TimeoutError("Database operation timed out")


@contextmanager
def time_limit(seconds):
    """Context manager to limit execution time on Unix systems."""
    # Note: signal.alarm only works on Unix/Linux, not Windows
    # On Windows, we rely on connect_timeout in connection string
    if hasattr(signal, 'SIGALRM'):
        signal.signal(signal.SIGALRM, timeout_handler)
        signal.alarm(seconds)
        try:
            yield
        finally:
            signal.alarm(0)
    else:
        # On Windows, just yield without timeout
        yield


def get_engine_with_timeout():
    """Create a new engine with connection timeout."""
    # Get latest DB URL (reloading config)
    url = get_database_url(force_reload=True)
    
    # Add connect_timeout to the connection URL
    if '?' in url:
        url += f"&connect_timeout={DB_TIMEOUT}"
    else:
        url += f"?connect_timeout={DB_TIMEOUT}"

    return create_engine(
        url,
        pool_pre_ping=True,
        pool_recycle=3600,
        connect_args={
            "connect_timeout": DB_TIMEOUT,
            "options": f"-c statement_timeout={DB_TIMEOUT * 1000}",  # milliseconds
            "prepare_threshold": None,  # Fix for psycopg3 bytes/string issue
        }
    )


@dataclass
class HealthCheckResult:
    """Result of a health check operation."""

    name: str
    passed: bool
    message: str
    details: Optional[str] = None


def check_connection() -> HealthCheckResult:
    """Test database connection with app user credentials.

    Returns:
        HealthCheckResult indicating connection status
    """
    try:
        engine = get_engine_with_timeout()
        with time_limit(DB_TIMEOUT):
            with engine.connect() as conn:
                # Simple query to test connection
                result = conn.execute(text("SELECT 1"))
                result.fetchone()
        engine.dispose()
        return HealthCheckResult(
            name="Connection",
            passed=True,
            message="App user can connect to database"
        )
    except TimeoutError:
        return HealthCheckResult(
            name="Connection",
            passed=False,
            message="Connection timeout - database not responding",
            details=f"Timed out after {DB_TIMEOUT} seconds"
        )
    except SQLAlchemyError as e:
        return HealthCheckResult(
            name="Connection",
            passed=False,
            message="Failed to connect to database",
            details=str(e)
        )
    except Exception as e:
        return HealthCheckResult(
            name="Connection",
            passed=False,
            message="Unexpected error during connection",
            details=str(e)
        )


def check_table_exists(table_name: str) -> HealthCheckResult:
    """Check if a table exists in the database.

    Args:
        table_name: Name of the table to check

    Returns:
        HealthCheckResult indicating table existence
    """
    try:
        engine = get_engine_with_timeout()
        with time_limit(DB_TIMEOUT):
            inspector = inspect(engine)
            table_exists = table_name in inspector.get_table_names()
        engine.dispose()

        if table_exists:
            return HealthCheckResult(
                name=f"Table: {table_name}",
                passed=True,
                message=f"Table '{table_name}' exists"
            )
        else:
            return HealthCheckResult(
                name=f"Table: {table_name}",
                passed=False,
                message=f"Table '{table_name}' does not exist",
                details="Run: python -m vulcanlab.data.init_db"
            )
    except TimeoutError:
        return HealthCheckResult(
            name=f"Table: {table_name}",
            passed=False,
            message=f"Timeout checking table '{table_name}'",
            details=f"Timed out after {DB_TIMEOUT} seconds"
        )
    except SQLAlchemyError as e:
        return HealthCheckResult(
            name=f"Table: {table_name}",
            passed=False,
            message=f"Error checking table '{table_name}'",
            details=str(e)
        )


def check_table_columns(table_name: str, required_columns: list[str]) -> HealthCheckResult:
    """Check if required columns exist in a table.

    Args:
        table_name: Name of the table
        required_columns: List of required column names

    Returns:
        HealthCheckResult indicating column existence
    """
    try:
        engine = get_engine_with_timeout()
        with time_limit(DB_TIMEOUT):
            inspector = inspect(engine)
            columns = [col["name"] for col in inspector.get_columns(table_name)]
            missing_columns = [col for col in required_columns if col not in columns]
        engine.dispose()

        if not missing_columns:
            return HealthCheckResult(
                name=f"Columns: {table_name}",
                passed=True,
                message=f"All required columns exist in '{table_name}'"
            )
        else:
            return HealthCheckResult(
                name=f"Columns: {table_name}",
                passed=False,
                message=f"Missing columns in '{table_name}': {', '.join(missing_columns)}",
                details="Run: python -m vulcanlab.data.init_db"
            )
    except TimeoutError:
        return HealthCheckResult(
            name=f"Columns: {table_name}",
            passed=False,
            message=f"Timeout checking columns in '{table_name}'",
            details=f"Timed out after {DB_TIMEOUT} seconds"
        )
    except SQLAlchemyError as e:
        return HealthCheckResult(
            name=f"Columns: {table_name}",
            passed=False,
            message=f"Error checking columns in '{table_name}'",
            details=str(e)
        )


def check_extension(extension_name: str) -> HealthCheckResult:
    """Check if a PostgreSQL extension is installed.

    Args:
        extension_name: Name of the extension

    Returns:
        HealthCheckResult indicating extension status
    """
    try:
        engine = get_engine_with_timeout()
        with time_limit(DB_TIMEOUT):
            with engine.connect() as conn:
                result = conn.execute(
                    text("SELECT 1 FROM pg_extension WHERE extname = :name"),
                    {"name": extension_name}
                )
                extension_exists = result.fetchone() is not None
        engine.dispose()

        if extension_exists:
            return HealthCheckResult(
                name=f"Extension: {extension_name}",
                passed=True,
                message=f"Extension '{extension_name}' is installed"
            )
        else:
            return HealthCheckResult(
                name=f"Extension: {extension_name}",
                passed=False,
                message=f"Extension '{extension_name}' is not installed",
                details="Run: python -m vulcanlab.data.init_db"
            )
    except TimeoutError:
        return HealthCheckResult(
            name=f"Extension: {extension_name}",
            passed=False,
            message=f"Timeout checking extension '{extension_name}'",
            details=f"Timed out after {DB_TIMEOUT} seconds"
        )
    except SQLAlchemyError as e:
        return HealthCheckResult(
            name=f"Extension: {extension_name}",
            passed=False,
            message=f"Error checking extension '{extension_name}'",
            details=str(e)
        )


def check_index(index_name: str, table_name: str) -> HealthCheckResult:
    """Check if an index exists on a table.

    Args:
        index_name: Name of the index
        table_name: Name of the table

    Returns:
        HealthCheckResult indicating index existence
    """
    try:
        engine = get_engine_with_timeout()
        with time_limit(DB_TIMEOUT):
            inspector = inspect(engine)
            indexes = [idx["name"] for idx in inspector.get_indexes(table_name)]
        engine.dispose()

        if index_name in indexes:
            return HealthCheckResult(
                name=f"Index: {index_name}",
                passed=True,
                message=f"Index '{index_name}' exists on '{table_name}'"
            )
        else:
            return HealthCheckResult(
                name=f"Index: {index_name}",
                passed=False,
                message=f"Index '{index_name}' does not exist on '{table_name}'",
                details="Run: python -m vulcanlab.data.init_db"
            )
    except TimeoutError:
        return HealthCheckResult(
            name=f"Index: {index_name}",
            passed=False,
            message=f"Timeout checking index '{index_name}'",
            details=f"Timed out after {DB_TIMEOUT} seconds"
        )
    except SQLAlchemyError as e:
        return HealthCheckResult(
            name=f"Index: {index_name}",
            passed=False,
            message=f"Error checking index '{index_name}'",
            details=str(e)
        )


def check_trigger(trigger_name: str, table_name: str) -> HealthCheckResult:
    """Check if a trigger exists on a table.

    Args:
        trigger_name: Name of the trigger
        table_name: Name of the table

    Returns:
        HealthCheckResult indicating trigger existence
    """
    try:
        engine = get_engine_with_timeout()
        with time_limit(DB_TIMEOUT):
            with engine.connect() as conn:
                result = conn.execute(
                    text("""
                        SELECT 1 FROM pg_trigger t
                        JOIN pg_class c ON t.tgrelid = c.oid
                        WHERE c.relname = :table_name AND t.tgname = :trigger_name
                    """),
                    {"table_name": table_name, "trigger_name": trigger_name}
                )
                trigger_exists = result.fetchone() is not None
        engine.dispose()

        if trigger_exists:
            return HealthCheckResult(
                name=f"Trigger: {trigger_name}",
                passed=True,
                message=f"Trigger '{trigger_name}' exists on '{table_name}'"
            )
        else:
            return HealthCheckResult(
                name=f"Trigger: {trigger_name}",
                passed=False,
                message=f"Trigger '{trigger_name}' does not exist on '{table_name}'",
                details="Run: python -m vulcanlab.data.init_db"
            )
    except TimeoutError:
        return HealthCheckResult(
            name=f"Trigger: {trigger_name}",
            passed=False,
            message=f"Timeout checking trigger '{trigger_name}'",
            details=f"Timed out after {DB_TIMEOUT} seconds"
        )
    except SQLAlchemyError as e:
        return HealthCheckResult(
            name=f"Trigger: {trigger_name}",
            passed=False,
            message=f"Error checking trigger '{trigger_name}'",
            details=str(e)
        )


def check_read_permission(table_name: str) -> HealthCheckResult:
    """Check if app user can read from a table.

    Args:
        table_name: Name of the table

    Returns:
        HealthCheckResult indicating read permission
    """
    try:
        engine = get_engine_with_timeout()
        with time_limit(DB_TIMEOUT):
            with engine.connect() as conn:
                result = conn.execute(text(f"SELECT 1 FROM {table_name} LIMIT 1"))
                result.fetchall()  # Don't care about results, just that it doesn't error
        engine.dispose()

        return HealthCheckResult(
            name=f"Read: {table_name}",
            passed=True,
            message=f"Can read from '{table_name}'"
        )
    except TimeoutError:
        return HealthCheckResult(
            name=f"Read: {table_name}",
            passed=False,
            message=f"Timeout reading from '{table_name}'",
            details=f"Timed out after {DB_TIMEOUT} seconds"
        )
    except SQLAlchemyError as e:
        return HealthCheckResult(
            name=f"Read: {table_name}",
            passed=False,
            message=f"Cannot read from '{table_name}'",
            details=str(e)
        )


def check_write_permission(table_name: str) -> HealthCheckResult:
    """Check if app user can write to a table.

    Args:
        table_name: Name of the table

    Returns:
        HealthCheckResult indicating write permission
    """
    try:
        engine = get_engine_with_timeout()
        with time_limit(DB_TIMEOUT):
            with engine.connect() as conn:
                # Try to start a transaction (tests write permission without actually writing)
                trans = conn.begin()
                # Check if we have INSERT privilege
                result = conn.execute(
                    text("""
                        SELECT has_table_privilege(current_user, :table_name, 'INSERT')
                    """),
                    {"table_name": table_name}
                )
                has_permission = result.fetchone()[0]
                trans.rollback()
        engine.dispose()

        if has_permission:
            return HealthCheckResult(
                name=f"Write: {table_name}",
                passed=True,
                message=f"Can write to '{table_name}'"
            )
        else:
            return HealthCheckResult(
                name=f"Write: {table_name}",
                passed=False,
                message=f"Cannot write to '{table_name}'",
                details="Missing INSERT privilege"
            )
    except TimeoutError:
        return HealthCheckResult(
            name=f"Write: {table_name}",
            passed=False,
            message=f"Timeout checking write permission on '{table_name}'",
            details=f"Timed out after {DB_TIMEOUT} seconds"
        )
    except SQLAlchemyError as e:
        return HealthCheckResult(
            name=f"Write: {table_name}",
            passed=False,
            message=f"Error checking write permission on '{table_name}'",
            details=str(e)
        )


def run_all_health_checks() -> list[HealthCheckResult]:
    """Run all database health checks.

    Returns:
        List of HealthCheckResult objects
    """
    results = []

    # Connection check
    results.append(check_connection())

    # Extension checks
    results.append(check_extension("vector"))

    # Table existence checks
    tables = ["works", "chunks", "queries", "results", "io_files", "prompt_templates", "prompt_meta", "rag_config"]
    for table in tables:
        results.append(check_table_exists(table))

    # Column checks - Core tables
    results.append(check_table_columns("works", [
        "id", "title", "authors", "year", "content_hash", "created_at", "updated_at"
    ]))
    results.append(check_table_columns("chunks", [
        "id", "work_id", "parent_id", "level", "content", "embedding",
        "start_line", "end_line", "vector_status"
    ]))
    results.append(check_table_columns("queries", [
        "id", "original_query", "embedding_original", "embedding_hyde",
        "vector_status", "created_at", "updated_at"
    ]))

    # Column checks - New tables
    results.append(check_table_columns("results", [
        "id", "query_id", "response_text", "created_at", "updated_at"
    ]))
    results.append(check_table_columns("io_files", [
        "id", "filename", "file_type", "file_path", "created_at", "updated_at", "last_seen_at"
    ]))
    results.append(check_table_columns("prompt_templates", [
        "id", "function_tag", "version", "title", "template_content", "is_active", "created_at", "updated_at"
    ]))
    results.append(check_table_columns("prompt_meta", [
        "id", "function_tag", "variables", "created_at", "updated_at"
    ]))
    results.append(check_table_columns("rag_config", [
        "id", "preset_name", "is_default", "description", "config", "created_at", "updated_at"
    ]))

    # Index checks - Vector indexes
    results.append(check_index("ix_chunks_embedding_hnsw", "chunks"))
    results.append(check_index("ix_queries_embedding_original_hnsw", "queries"))
    results.append(check_index("ix_queries_embedding_hyde_hnsw", "queries"))
    results.append(check_index("ix_chunks_content_tsvector_gin", "chunks"))

    # Index checks - New tables
    results.append(check_index("idx_prompt_meta_function_tag", "prompt_meta"))
    results.append(check_index("idx_rag_config_preset_name", "rag_config"))
    results.append(check_index("idx_rag_config_is_default", "rag_config"))
    results.append(check_index("idx_prompt_templates_function_tag", "prompt_templates"))
    results.append(check_index("idx_prompt_templates_active", "prompt_templates"))

    # Trigger checks
    results.append(check_trigger("tsvector_update", "chunks"))
    results.append(check_trigger("trigger_update_prompt_meta_updated_at", "prompt_meta"))
    results.append(check_trigger("trigger_update_rag_config_updated_at", "rag_config"))
    results.append(check_trigger("trigger_ensure_single_default_rag_config", "rag_config"))

    # Permission checks
    for table in tables:
        results.append(check_read_permission(table))
        results.append(check_write_permission(table))

    return results
