import json
import pytest
from pathlib import Path

def test_docker_config_exists():
    """Verify vulcanlab.config.docker.json exists and is valid JSON."""
    config_path = Path("vulcanlab.config.docker.json")
    assert config_path.exists(), "vulcanlab.config.docker.json not found"

    with open(config_path) as f:
        config = json.load(f)

    assert "database" in config
    assert "llm" in config
    assert "paths" in config

def test_docker_config_database_settings():
    """Verify database configuration uses correct internal settings."""
    with open("vulcanlab.config.docker.json") as f:
        config = json.load(f)

    db = config["database"]
    assert db["host"] == "localhost", "Database should use localhost in container"
    assert db["port"] == 5432
    assert db["db_name"] == "vulcanlab_test"

def test_docker_config_paths_are_absolute():
    """Verify paths use absolute container paths."""
    with open("vulcanlab.config.docker.json") as f:
        config = json.load(f)

    paths = config["paths"]
    assert paths["input_dir"].startswith("/app/")
    assert paths["output_dir"].startswith("/app/")

def test_env_template_exists():
    """Verify .env.docker.example template exists."""
    env_template = Path(".env.docker.example")
    assert env_template.exists(), ".env.docker.example template not found"

    content = env_template.read_text()
    assert "POSTGRES_PASSWORD" in content
    assert "LLM_GOOGLE_API_KEY" in content

def test_dockerignore_excludes_sensitive_files():
    """Verify .dockerignore excludes secrets and dev files."""
    dockerignore = Path(".dockerignore")
    assert dockerignore.exists(), ".dockerignore not found"

    content = dockerignore.read_text()
    assert ".env" in content
    assert "venv/" in content
    assert "node_modules/" in content
    assert ".git/" in content
