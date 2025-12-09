"""Configuration for LLM providers.

Provider and model settings are loaded from vulcanlab.config.json.
API keys (secrets) are loaded from .env file.
"""

from enum import Enum
from pathlib import Path

from pydantic_settings import BaseSettings, SettingsConfigDict

from vulcanlab.config import load_config


def _find_env_file() -> Path | None:
    """Find the .env file by searching up from this file's location."""
    current = Path(__file__).resolve().parent
    # Search up to find .env in project root
    for _ in range(10):  # Limit search depth
        env_file = current / ".env"
        if env_file.exists():
            return env_file
        if current.parent == current:
            break
        current = current.parent
    return None


# Cache the env file path at module load time
_ENV_FILE_PATH = _find_env_file()


class LLMProvider(str, Enum):
    OPENAI = "openai"
    GEMINI = "gemini"


class ModelTier(str, Enum):
    LIGHT = "light"
    FULL = "full"


class LLMSettings(BaseSettings):
    """LLM provider configuration.

    Provider and model names are loaded from vulcanlab.config.json.
    API keys (secrets) are loaded from .env file.
    """

    # API Keys from .env (secrets)
    openai_api_key: str | None = None
    google_api_key: str | None = None

    model_config = SettingsConfigDict(
        env_prefix="LLM_",
        env_file=_ENV_FILE_PATH,
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore",
    )

    @property
    def provider(self) -> LLMProvider:
        """Get the active LLM provider from JSON config."""
        app_config = load_config()
        return LLMProvider(app_config.llm.provider)

    def get_model(self, tier: ModelTier = ModelTier.LIGHT) -> str:
        """Get the model name for the current provider and tier.

        Args:
            tier: Model tier (LIGHT or FULL)

        Returns:
            Model name string
        """
        app_config = load_config()

        if self.provider == LLMProvider.OPENAI:
            return (
                app_config.llm.models.openai.light
                if tier == ModelTier.LIGHT
                else app_config.llm.models.openai.full
            )
        elif self.provider == LLMProvider.GEMINI:
            return (
                app_config.llm.models.gemini.light
                if tier == ModelTier.LIGHT
                else app_config.llm.models.gemini.full
            )
        else:
            raise ValueError(f"Unsupported provider: {self.provider}")
