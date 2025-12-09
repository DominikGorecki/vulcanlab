"""
API Configuration settings.

Uses pydantic-settings for environment variables and JSON config for paths.
"""

from functools import lru_cache
from pathlib import Path

from pydantic_settings import BaseSettings, SettingsConfigDict

from vulcanlab.config import load_config


class APISettings(BaseSettings):
    """API configuration loaded from environment variables and JSON config."""

    model_config = SettingsConfigDict(
        env_prefix="vulcanlab_api_",
        env_file=".env",
        extra="ignore",  # Ignore extra env vars from .env
    )

    # API metadata
    api_title: str = "VulcanLab API"
    api_description: str = """
## VulcanLab REST API

A Retrieval-Augmented Generation system for psychology literature.

### Features

* **Document Conversion** - Convert EPUBs, PDFs to markdown
* **Sanitization** - Clean and normalize content
* **Chunking** - Split documents into semantic chunks
* **Vectorization** - Generate embeddings for chunks
* **RAG** - Query and generate responses with context

### Authentication

Currently no authentication required (development mode).
"""
    api_version: str = "0.1.0"

    # Server settings
    debug: bool = False

    # CORS settings
    cors_origins: list[str] = [
        "http://localhost:3000",
        "http://127.0.0.1:3000",
    ]
    cors_allow_credentials: bool = True
    cors_allow_methods: list[str] = ["*"]
    cors_allow_headers: list[str] = ["*"]

    @property
    def input_dir(self) -> Path:
        """Get input directory path from JSON config.

        Returns:
            Absolute Path object for input directory

        Raises:
            ValueError: If path is not absolute or doesn't exist
        """
        app_config = load_config()
        input_path = Path(app_config.paths.input_dir)

        if not input_path.is_absolute():
            raise ValueError(f"input_dir must be an absolute path, got: {input_path}")

        if not input_path.exists():
            raise ValueError(f"input_dir does not exist: {input_path}")

        return input_path

    @property
    def output_dir(self) -> Path:
        """Get output directory path from JSON config.

        Returns:
            Absolute Path object for output directory

        Raises:
            ValueError: If path is not absolute or doesn't exist
        """
        app_config = load_config()
        output_path = Path(app_config.paths.output_dir)

        if not output_path.is_absolute():
            raise ValueError(f"output_dir must be an absolute path, got: {output_path}")

        if not output_path.exists():
            raise ValueError(f"output_dir does not exist: {output_path}")

        return output_path


@lru_cache
def get_settings() -> APISettings:
    """Get cached settings instance."""
    return APISettings()

