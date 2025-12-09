import os
import pytest
from pathlib import Path

def test_init_db_script_exists():
    """Verify docker/init-db.sh exists."""
    script = Path("docker/init-db.sh")
    assert script.exists(), "docker/init-db.sh not found"

def test_init_db_script_has_shebang():
    """Verify init-db.sh has bash shebang."""
    with open("docker/init-db.sh") as f:
        first_line = f.readline()
        assert first_line.strip() == "#!/bin/bash"

def test_init_db_script_has_error_handling():
    """Verify init-db.sh uses set -e for error handling."""
    with open("docker/init-db.sh") as f:
        content = f.read()
        assert "set -e" in content

def test_init_db_script_uses_env_vars():
    """Verify init-db.sh uses environment variables with defaults."""
    with open("docker/init-db.sh") as f:
        content = f.read()
        assert "POSTGRES_DB:-vulcanlab_test" in content
        assert "POSTGRES_APP_USER:-vulcanlab_app_user_test" in content
        assert "POSTGRES_APP_PASSWORD" in content

def test_init_db_script_creates_database():
    """Verify init-db.sh creates database."""
    with open("docker/init-db.sh") as f:
        content = f.read()
        assert "CREATE DATABASE" in content

def test_init_db_script_creates_user():
    """Verify init-db.sh creates application user."""
    with open("docker/init-db.sh") as f:
        content = f.read()
        assert "CREATE USER" in content
        assert "GRANT" in content

def test_init_db_script_enables_extensions():
    """Verify init-db.sh enables vector and age extensions."""
    with open("docker/init-db.sh") as f:
        content = f.read()
        assert "CREATE EXTENSION IF NOT EXISTS vector" in content
        assert "CREATE EXTENSION IF NOT EXISTS age" in content
        assert "LOAD 'age'" in content

def test_init_db_script_sets_search_path():
    """Verify init-db.sh sets search path for AGE."""
    with open("docker/init-db.sh") as f:
        content = f.read()
        assert "ALTER DATABASE" in content
        assert "search_path" in content
        assert "ag_catalog" in content

def test_enable_extensions_sql_exists():
    """Verify enable-extensions.sql exists in docker directory."""
    sql_file = Path("docker/enable-extensions.sql")
    assert sql_file.exists(), "docker/enable-extensions.sql not found"

def test_enable_extensions_sql_has_vector():
    """Verify enable-extensions.sql includes vector extension."""
    with open("docker/enable-extensions.sql") as f:
        content = f.read()
        assert "CREATE EXTENSION IF NOT EXISTS vector" in content

def test_enable_extensions_sql_has_age():
    """Verify enable-extensions.sql includes AGE extension."""
    with open("docker/enable-extensions.sql") as f:
        content = f.read()
        assert "CREATE EXTENSION IF NOT EXISTS age" in content
        assert "LOAD 'age'" in content

def test_entrypoint_has_initdb_logic():
    """Verify docker-entrypoint.sh includes database initialization logic."""
    with open("docker-entrypoint.sh") as f:
        content = f.read()
        assert "initdb" in content
        assert "/docker-entrypoint-initdb.d/" in content
        assert "pg_ctl" in content

def test_entrypoint_starts_temp_postgres():
    """Verify entrypoint starts temporary PostgreSQL for initialization."""
    with open("docker-entrypoint.sh") as f:
        content = f.read()
        assert "pg_ctl" in content
        assert "start" in content
        assert "stop" in content

def test_entrypoint_configures_pg_hba():
    """Verify entrypoint configures pg_hba.conf."""
    with open("docker-entrypoint.sh") as f:
        content = f.read()
        assert "pg_hba.conf" in content
        assert "md5" in content

def test_entrypoint_checks_app_password():
    """Verify entrypoint checks for POSTGRES_APP_PASSWORD."""
    with open("docker-entrypoint.sh") as f:
        content = f.read()
        assert "POSTGRES_APP_PASSWORD" in content

def test_dockerfile_copies_init_scripts():
    """Verify Dockerfile copies init scripts to /docker-entrypoint-initdb.d/."""
    with open("Dockerfile.allinone") as f:
        content = f.read()
        assert "/docker-entrypoint-initdb.d/" in content
        assert "init-db.sh" in content
        assert "enable-extensions.sql" in content

def test_dockerfile_creates_initdb_directory():
    """Verify Dockerfile creates /docker-entrypoint-initdb.d/ directory."""
    with open("Dockerfile.allinone") as f:
        content = f.read()
        assert "mkdir -p" in content
        assert "/docker-entrypoint-initdb.d" in content

def test_env_example_has_app_password():
    """Verify .env.docker.example includes POSTGRES_APP_PASSWORD."""
    with open(".env.docker.example") as f:
        content = f.read()
        assert "POSTGRES_APP_PASSWORD" in content
