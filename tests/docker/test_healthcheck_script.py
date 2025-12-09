import pytest
from pathlib import Path
import subprocess

def test_healthcheck_script_exists():
    """Verify healthcheck.py exists."""
    script = Path("scripts/healthcheck.py")
    assert script.exists(), "scripts/healthcheck.py not found"

def test_healthcheck_has_shebang():
    """Verify healthcheck.py has python shebang."""
    with open("scripts/healthcheck.py") as f:
        first_line = f.readline()
        assert first_line.strip() in ["#!/usr/bin/env python3", "#!/usr/bin/python3"]

def test_healthcheck_syntax_valid():
    """Verify healthcheck.py has valid Python syntax."""
    result = subprocess.run(
        ["python3", "-m", "py_compile", "scripts/healthcheck.py"],
        capture_output=True
    )
    assert result.returncode == 0, f"Syntax error: {result.stderr.decode()}"

def test_healthcheck_has_main_function():
    """Verify healthcheck.py has main function."""
    with open("scripts/healthcheck.py") as f:
        content = f.read()
        assert "def main():" in content

def test_healthcheck_has_check_functions():
    """Verify healthcheck.py has all required check functions."""
    with open("scripts/healthcheck.py") as f:
        content = f.read()
        assert "def check_supervisord(" in content
        assert "def check_postgresql(" in content
        assert "def check_backend_api(" in content
        assert "def check_frontend(" in content
        assert "def check_database_extensions(" in content

def test_healthcheck_has_exit_codes():
    """Verify healthcheck.py uses proper exit codes."""
    with open("scripts/healthcheck.py") as f:
        content = f.read()
        assert "return 0" in content  # Success
        assert "return 1" in content  # Failure

def test_healthcheck_has_troubleshooting():
    """Verify healthcheck.py includes troubleshooting help."""
    with open("scripts/healthcheck.py") as f:
        content = f.read()
        assert "print_troubleshooting" in content
        assert "supervisorctl" in content

def test_quick_health_script_exists():
    """Verify quick-health.sh exists."""
    script = Path("scripts/quick-health.sh")
    assert script.exists(), "scripts/quick-health.sh not found"

def test_quick_health_has_bash_shebang():
    """Verify quick-health.sh has bash shebang."""
    with open("scripts/quick-health.sh") as f:
        first_line = f.readline()
        assert first_line.startswith("#!/bin/bash")

def test_quick_health_checks_backend():
    """Verify quick-health.sh checks backend."""
    with open("scripts/quick-health.sh") as f:
        content = f.read()
        assert "localhost:8000" in content

def test_quick_health_checks_frontend():
    """Verify quick-health.sh checks frontend."""
    with open("scripts/quick-health.sh") as f:
        content = f.read()
        assert "localhost:3000" in content

def test_dockerfile_copies_scripts():
    """Verify Dockerfile copies scripts directory."""
    with open("Dockerfile.allinone") as f:
        content = f.read()
        assert "COPY scripts/" in content
        assert "/app/scripts/" in content

def test_dockerfile_sets_script_permissions():
    """Verify Dockerfile sets executable permissions on scripts."""
    with open("Dockerfile.allinone") as f:
        content = f.read()
        assert "chmod +x" in content
        assert "healthcheck.py" in content
