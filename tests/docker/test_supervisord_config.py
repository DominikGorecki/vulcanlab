import configparser
import pytest
from pathlib import Path

def test_supervisord_conf_exists():
    """Verify supervisord.conf exists."""
    config_path = Path("supervisord.conf")
    assert config_path.exists(), "supervisord.conf not found"

def test_supervisord_conf_structure():
    """Verify supervisord.conf has required sections."""
    config = configparser.ConfigParser()
    config.read("supervisord.conf")

    # Check required sections
    assert "supervisord" in config.sections()
    assert "program:postgresql" in config.sections()
    assert "program:backend" in config.sections()
    assert "program:frontend" in config.sections()

def test_postgresql_program_config():
    """Verify PostgreSQL program configuration."""
    config = configparser.ConfigParser()
    config.read("supervisord.conf")

    pg = config["program:postgresql"]
    assert pg["user"] == "postgres"
    assert pg["autostart"] == "true"
    assert pg["autorestart"] == "true"
    assert pg["priority"] == "1", "PostgreSQL should start first"
    assert "/usr/lib/postgresql/16/bin/postgres" in pg["command"]

def test_backend_program_config():
    """Verify backend (FastAPI) program configuration."""
    config = configparser.ConfigParser()
    config.read("supervisord.conf")

    backend = config["program:backend"]
    assert backend["autostart"] == "true"
    assert backend["autorestart"] == "true"
    assert backend["priority"] == "10", "Backend should start after PostgreSQL"
    assert "uvicorn" in backend["command"]
    assert "vulcanlab_api.main:app" in backend["command"]
    assert "--port 8000" in backend["command"]

    # Check environment variables
    env = backend["environment"]
    assert "PYTHONPATH" in env
    assert "VULCANLAB_CONFIG" in env

def test_frontend_program_config():
    """Verify frontend (Next.js) program configuration."""
    config = configparser.ConfigParser()
    config.read("supervisord.conf")

    frontend = config["program:frontend"]
    assert frontend["autostart"] == "true"
    assert frontend["autorestart"] == "true"
    assert frontend["priority"] == "20", "Frontend should start after backend"
    assert "node" in frontend["command"]
    assert "server.js" in frontend["command"]

    # Check environment variables
    env = frontend["environment"]
    assert "NODE_ENV" in env
    assert "PORT" in env

def test_log_rotation_configured():
    """Verify log rotation is properly configured for all programs."""
    config = configparser.ConfigParser()
    config.read("supervisord.conf")

    programs = ["program:postgresql", "program:backend", "program:frontend"]

    for program in programs:
        prog_config = config[program]

        # Check log files are defined
        assert "stdout_logfile" in prog_config
        assert "stderr_logfile" in prog_config

        # Check rotation settings
        assert prog_config.get("stdout_logfile_maxbytes") == "50MB"
        assert prog_config.get("stderr_logfile_maxbytes") == "50MB"
        assert prog_config.get("stdout_logfile_backups") == "10"
        assert prog_config.get("stderr_logfile_backups") == "10"

def test_startup_priority_ordering():
    """Verify programs start in correct order (PostgreSQL → Backend → Frontend)."""
    config = configparser.ConfigParser()
    config.read("supervisord.conf")

    pg_priority = int(config["program:postgresql"]["priority"])
    backend_priority = int(config["program:backend"]["priority"])
    frontend_priority = int(config["program:frontend"]["priority"])

    assert pg_priority < backend_priority, "PostgreSQL must start before backend"
    assert backend_priority < frontend_priority, "Backend must start before frontend"

def test_docker_entrypoint_exists():
    """Verify docker-entrypoint.sh exists and is executable."""
    entrypoint_path = Path("docker-entrypoint.sh")
    assert entrypoint_path.exists(), "docker-entrypoint.sh not found"

    # Check it's a shell script
    with open(entrypoint_path) as f:
        first_line = f.readline()
        assert first_line.startswith("#!/bin/bash"), "Must be a bash script"

def test_docker_entrypoint_has_postgres_check():
    """Verify entrypoint script checks for PostgreSQL initialization."""
    with open("docker-entrypoint.sh") as f:
        content = f.read()

    assert "PG_VERSION" in content, "Should check for PostgreSQL initialization"
    assert "initdb" in content, "Should initialize PostgreSQL if needed"
    assert "shared_preload_libraries" in content, "Should configure AGE extension"

def test_docker_entrypoint_validates_env_vars():
    """Verify entrypoint script validates required environment variables."""
    with open("docker-entrypoint.sh") as f:
        content = f.read()

    assert "POSTGRES_PASSWORD" in content, "Should check for POSTGRES_PASSWORD"
    assert "LLM_GOOGLE_API_KEY" in content or "LLM_OPENAI_API_KEY" in content, \
        "Should check for LLM API keys"

def test_dockerfile_includes_supervisord_files():
    """Verify Dockerfile.allinone includes supervisord configuration."""
    with open("Dockerfile.allinone") as f:
        content = f.read()

    assert "COPY supervisord.conf" in content, "Should copy supervisord.conf"
    assert "COPY docker-entrypoint.sh" in content, "Should copy entrypoint script"
    assert "ENTRYPOINT" in content, "Should set ENTRYPOINT"
    assert "supervisord" in content, "Should run supervisord"
