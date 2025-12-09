import pytest
from pathlib import Path

def test_installation_guide_exists():
    """Verify INSTALLATION.md exists."""
    doc = Path("docs/INSTALLATION.md")
    assert doc.exists(), "docs/INSTALLATION.md not found"

def test_docker_hub_guide_exists():
    """Verify DOCKER_HUB_DEPLOYMENT.md exists."""
    doc = Path("docs/DOCKER_HUB_DEPLOYMENT.md")
    assert doc.exists(), "docs/DOCKER_HUB_DEPLOYMENT.md not found"

def test_troubleshooting_guide_exists():
    """Verify TROUBLESHOOTING.md exists."""
    doc = Path("docs/TROUBLESHOOTING.md")
    assert doc.exists(), "docs/TROUBLESHOOTING.md not found"

def test_build_script_exists():
    """Verify build-and-package.sh exists."""
    script = Path("scripts/build-and-package.sh")
    assert script.exists(), "scripts/build-and-package.sh not found"

def test_quick_start_script_exists():
    """Verify quick-start.sh exists."""
    script = Path("scripts/quick-start.sh")
    assert script.exists(), "scripts/quick-start.sh not found"

def test_env_example_exists():
    """Verify .env.docker.example exists."""
    env = Path(".env.docker.example")
    assert env.exists(), ".env.docker.example not found"

def test_build_script_is_executable():
    """Verify build-and-package.sh is executable."""
    script = Path("scripts/build-and-package.sh")
    assert script.exists()
    # Check if file has execute permission
    import os
    assert os.access(script, os.X_OK), "build-and-package.sh is not executable"

def test_quick_start_script_is_executable():
    """Verify quick-start.sh is executable."""
    script = Path("scripts/quick-start.sh")
    assert script.exists()
    # Check if file has execute permission
    import os
    assert os.access(script, os.X_OK), "quick-start.sh is not executable"

def test_installation_guide_has_prerequisites():
    """Verify installation guide includes prerequisites section."""
    with open("docs/INSTALLATION.md") as f:
        content = f.read()
        assert "Prerequisites" in content
        assert "Docker Desktop" in content
        assert "API Keys" in content

def test_installation_guide_has_methods():
    """Verify installation guide has all installation methods."""
    with open("docs/INSTALLATION.md") as f:
        content = f.read()
        assert "Method A" in content
        assert "Method B" in content
        assert "Method C" in content

def test_docker_hub_guide_has_release_process():
    """Verify Docker Hub guide includes release process."""
    with open("docs/DOCKER_HUB_DEPLOYMENT.md") as f:
        content = f.read()
        assert "Release Process" in content
        assert "docker push" in content
        assert "docker build" in content

def test_troubleshooting_guide_has_sections():
    """Verify troubleshooting guide has all major sections."""
    with open("docs/TROUBLESHOOTING.md") as f:
        content = f.read()
        assert "Installation Issues" in content
        assert "Service Issues" in content
        assert "Database Issues" in content
        assert "Performance Issues" in content
