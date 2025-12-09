"""
Unit tests for application configuration module.

Tests config model validation, config loading from file, config saving to file,
default config generation, config path resolution, and error handling for invalid configs.

Usage:
    pytest tests/unit/test_app_config.py -v
"""

import pytest
from unittest.mock import Mock, MagicMock, patch, mock_open
from pathlib import Path
from tempfile import TemporaryDirectory
import json

from vulcanlab.config.app_config import (
    AppConfig,
    DatabaseConfig,
    LLMConfig,
    LLMModelsConfig,
    ModelConfig,
    PathsConfig,
    get_config_path,
    get_default_config,
    load_config,
    save_config,
)


@pytest.fixture(autouse=True)
def clear_config_cache():
    """Clear config cache before each test."""
    import vulcanlab.config.app_config as app_config_module
    app_config_module._config_cache = None
    yield
    # Clear cache after test too
    app_config_module._config_cache = None


class TestDatabaseConfig:
    """Tests for DatabaseConfig model."""

    def test_database_config_defaults(self):
        """Test DatabaseConfig with default values."""
        config = DatabaseConfig()
        assert config.admin_user == "postgres"
        assert config.host == "127.0.0.1"
        assert config.port == 5432
        assert config.db_name == "psych_rag_test"
        assert config.app_user == "psych_rag_app_user_test"

    def test_database_config_custom_values(self):
        """Test DatabaseConfig with custom values."""
        config = DatabaseConfig(
            admin_user="admin",
            host="localhost",
            port=3306,
            db_name="test_db",
            app_user="app_user"
        )
        assert config.admin_user == "admin"
        assert config.host == "localhost"
        assert config.port == 3306
        assert config.db_name == "test_db"
        assert config.app_user == "app_user"


class TestModelConfig:
    """Tests for ModelConfig model."""

    def test_model_config_creation(self):
        """Test ModelConfig creation."""
        config = ModelConfig(light="gpt-3.5-turbo", full="gpt-4")
        assert config.light == "gpt-3.5-turbo"
        assert config.full == "gpt-4"

    def test_model_config_required_fields(self):
        """Test that ModelConfig requires both light and full."""
        with pytest.raises(Exception):  # Pydantic validation error
            ModelConfig(light="gpt-3.5-turbo")  # Missing full


class TestLLMModelsConfig:
    """Tests for LLMModelsConfig model."""

    def test_llm_models_config_defaults(self):
        """Test LLMModelsConfig with default values."""
        config = LLMModelsConfig()
        assert config.openai.light == "gpt-4o-mini"
        assert config.openai.full == "gpt-4o"
        assert config.gemini.light == "gemini-flash-latest"
        assert config.gemini.full == "gemini-2.5-pro"

    def test_llm_models_config_custom_values(self):
        """Test LLMModelsConfig with custom values."""
        openai_config = ModelConfig(light="gpt-3.5-turbo", full="gpt-4")
        gemini_config = ModelConfig(light="gemini-pro", full="gemini-ultra")
        config = LLMModelsConfig(openai=openai_config, gemini=gemini_config)
        assert config.openai.light == "gpt-3.5-turbo"
        assert config.openai.full == "gpt-4"
        assert config.gemini.light == "gemini-pro"
        assert config.gemini.full == "gemini-ultra"


class TestLLMConfig:
    """Tests for LLMConfig model."""

    def test_llm_config_defaults(self):
        """Test LLMConfig with default values."""
        config = LLMConfig()
        assert config.provider == "gemini"
        assert isinstance(config.models, LLMModelsConfig)

    def test_llm_config_custom_provider(self):
        """Test LLMConfig with custom provider."""
        config = LLMConfig(provider="openai")
        assert config.provider == "openai"

    def test_llm_config_invalid_provider(self):
        """Test that invalid provider raises validation error."""
        with pytest.raises(Exception):  # Pydantic validation error
            LLMConfig(provider="invalid")


class TestPathsConfig:
    """Tests for PathsConfig model."""

    def test_paths_config_defaults(self):
        """Test PathsConfig with default values."""
        config = PathsConfig()
        assert "input" in config.input_dir.lower()
        assert "output" in config.output_dir.lower()

    def test_paths_config_custom_values(self):
        """Test PathsConfig with custom values."""
        config = PathsConfig(
            input_dir="/custom/input",
            output_dir="/custom/output"
        )
        assert config.input_dir == "/custom/input"
        assert config.output_dir == "/custom/output"

    def test_paths_config_validate_paths_absolute(self):
        """Test path validation for absolute paths."""
        # Use platform-appropriate absolute paths
        import os
        if os.name == 'nt':  # Windows
            input_dir = "C:\\absolute\\input"
            output_dir = "C:\\absolute\\output"
        else:  # Unix
            input_dir = "/absolute/input"
            output_dir = "/absolute/output"
        
        config = PathsConfig(
            input_dir=input_dir,
            output_dir=output_dir
        )
        # Should not raise
        config.validate_paths_absolute()

    def test_paths_config_validate_paths_relative_raises(self):
        """Test that relative paths raise ValueError."""
        config = PathsConfig(
            input_dir="relative/input",
            output_dir="/absolute/output"
        )
        with pytest.raises(ValueError, match="must be an absolute path"):
            config.validate_paths_absolute()

    def test_paths_config_validate_paths_relative_output_raises(self):
        """Test that relative output path raises ValueError."""
        config = PathsConfig(
            input_dir="/absolute/input",
            output_dir="relative/output"
        )
        with pytest.raises(ValueError, match="must be an absolute path"):
            config.validate_paths_absolute()


class TestAppConfig:
    """Tests for AppConfig model."""

    def test_app_config_defaults(self):
        """Test AppConfig with default values."""
        config = AppConfig()
        assert isinstance(config.database, DatabaseConfig)
        assert isinstance(config.llm, LLMConfig)
        assert isinstance(config.paths, PathsConfig)

    def test_app_config_custom_values(self):
        """Test AppConfig with custom values."""
        db_config = DatabaseConfig(host="custom_host")
        llm_config = LLMConfig(provider="openai")
        paths_config = PathsConfig(input_dir="/custom/input")
        
        config = AppConfig(
            database=db_config,
            llm=llm_config,
            paths=paths_config
        )
        assert config.database.host == "custom_host"
        assert config.llm.provider == "openai"
        assert config.paths.input_dir == "/custom/input"

    def test_app_config_model_dump(self):
        """Test that AppConfig can be dumped to dict."""
        config = AppConfig()
        dumped = config.model_dump()
        assert isinstance(dumped, dict)
        assert "database" in dumped
        assert "llm" in dumped
        assert "paths" in dumped


class TestGetConfigPath:
    """Tests for get_config_path() function."""

    def test_get_config_path_finds_file(self):
        """Test that get_config_path finds existing config file."""
        # Create a temporary config file
        with TemporaryDirectory() as tmpdir:
            config_file = Path(tmpdir) / "vulcanlab.config.json"
            config_file.write_text("{}", encoding='utf-8')
            
            # Mock the module's __file__ to point to a file in tmpdir
            with patch('vulcanlab.config.app_config.__file__', str(Path(tmpdir) / "app_config.py")):
                result = get_config_path()
                assert result.name == "vulcanlab.config.json"
                assert result.exists()

    def test_get_config_path_not_found_returns_default(self):
        """Test that get_config_path returns default path when file not found."""
        # Create a temporary directory without config file
        with TemporaryDirectory() as tmpdir:
            # Mock the module's __file__ to point to a file in tmpdir
            with patch('vulcanlab.config.app_config.__file__', str(Path(tmpdir) / "app_config.py")):
                result = get_config_path()
                assert result.name == "vulcanlab.config.json"
                # Should return a path even if file doesn't exist
                # The path will be calculated based on __file__ location


class TestGetDefaultConfig:
    """Tests for get_default_config() function."""

    def test_get_default_config_returns_app_config(self):
        """Test that get_default_config returns AppConfig instance."""
        config = get_default_config()
        assert isinstance(config, AppConfig)

    def test_get_default_config_has_defaults(self):
        """Test that default config has expected default values."""
        config = get_default_config()
        assert config.database.host == "127.0.0.1"
        assert config.llm.provider == "gemini"
        assert "input" in config.paths.input_dir.lower()


class TestLoadConfig:
    """Tests for load_config() function."""

    def test_load_config_file_not_found_returns_default(self):
        """Test that load_config returns default when file doesn't exist."""
        with patch('vulcanlab.config.app_config.get_config_path') as mock_get_path:
            mock_path = MagicMock(spec=Path)
            mock_path.exists.return_value = False
            mock_get_path.return_value = mock_path
            
            config = load_config()
            assert isinstance(config, AppConfig)

    def test_load_config_loads_from_file(self):
        """Test that load_config loads from JSON file."""
        config_data = {
            "database": {
                "host": "custom_host",
                "port": 3306
            },
            "llm": {
                "provider": "openai"
            },
            "paths": {
                "input_dir": "/custom/input",
                "output_dir": "/custom/output"
            }
        }
        
        with patch('vulcanlab.config.app_config.get_config_path') as mock_get_path, \
             patch('builtins.open', mock_open(read_data=json.dumps(config_data))):
            mock_path = MagicMock(spec=Path)
            mock_path.exists.return_value = True
            mock_get_path.return_value = mock_path
            
            config = load_config()
            assert config.database.host == "custom_host"
            assert config.database.port == 3306
            assert config.llm.provider == "openai"
            assert config.paths.input_dir == "/custom/input"

    def test_load_config_invalid_json_raises_error(self):
        """Test that invalid JSON raises ValueError."""
        with patch('vulcanlab.config.app_config.get_config_path') as mock_get_path, \
             patch('builtins.open', mock_open(read_data="invalid json {")):
            mock_path = MagicMock(spec=Path)
            mock_path.exists.return_value = True
            mock_get_path.return_value = mock_path
            
            with pytest.raises(ValueError, match="Invalid JSON"):
                load_config()

    def test_load_config_invalid_schema_raises_error(self):
        """Test that invalid schema raises ValueError."""
        config_data = {
            "database": {
                "port": "not_a_number"  # Invalid type
            }
        }
        
        with patch('vulcanlab.config.app_config.get_config_path') as mock_get_path, \
             patch('builtins.open', mock_open(read_data=json.dumps(config_data))):
            mock_path = MagicMock(spec=Path)
            mock_path.exists.return_value = True
            mock_get_path.return_value = mock_path
            
            with pytest.raises(ValueError, match="Error loading config"):
                load_config()

    def test_load_config_caching(self):
        """Test that load_config caches the result."""
        config_data = {
            "database": {"host": "cached_host"}
        }
        
        with patch('vulcanlab.config.app_config.get_config_path') as mock_get_path, \
             patch('builtins.open', mock_open(read_data=json.dumps(config_data))):
            mock_path = MagicMock(spec=Path)
            mock_path.exists.return_value = True
            mock_get_path.return_value = mock_path
            
            config1 = load_config()
            config2 = load_config()
            
            # Should return same instance (cached)
            assert config1 is config2
            # get_config_path should only be called once
            assert mock_get_path.call_count == 1

    def test_load_config_force_reload(self):
        """Test that force_reload bypasses cache."""
        config_data1 = {
            "database": {"host": "host1"}
        }
        config_data2 = {
            "database": {"host": "host2"}
        }
        
        with patch('vulcanlab.config.app_config.get_config_path') as mock_get_path:
            mock_path = MagicMock(spec=Path)
            mock_path.exists.return_value = True
            mock_get_path.return_value = mock_path
            
            with patch('builtins.open', mock_open(read_data=json.dumps(config_data1))):
                config1 = load_config()
            
            with patch('builtins.open', mock_open(read_data=json.dumps(config_data2))):
                config2 = load_config(force_reload=True)
            
            # Should reload and get new data
            assert config2.database.host == "host2"


class TestSaveConfig:
    """Tests for save_config() function."""

    def test_save_config_writes_to_file(self):
        """Test that save_config writes config to file."""
        config = AppConfig()
        config.database.host = "saved_host"
        
        with TemporaryDirectory() as tmpdir:
            config_file = Path(tmpdir) / "vulcanlab.config.json"
            
            with patch('vulcanlab.config.app_config.get_config_path') as mock_get_path:
                mock_get_path.return_value = config_file
                
                save_config(config)
                
                assert config_file.exists()
                loaded_data = json.loads(config_file.read_text(encoding='utf-8'))
                assert loaded_data["database"]["host"] == "saved_host"

    def test_save_config_creates_parent_directories(self):
        """Test that save_config creates parent directories if needed."""
        config = AppConfig()
        
        with TemporaryDirectory() as tmpdir:
            config_file = Path(tmpdir) / "nested" / "dir" / "vulcanlab.config.json"
            
            with patch('vulcanlab.config.app_config.get_config_path') as mock_get_path:
                mock_get_path.return_value = config_file
                
                save_config(config)
                
                assert config_file.exists()
                assert config_file.parent.exists()

    def test_save_config_updates_cache(self):
        """Test that save_config updates the cache."""
        config = AppConfig()
        config.database.host = "cached_host"
        
        with TemporaryDirectory() as tmpdir:
            config_file = Path(tmpdir) / "vulcanlab.config.json"
            
            with patch('vulcanlab.config.app_config.get_config_path') as mock_get_path:
                mock_get_path.return_value = config_file
                
                save_config(config)
                
                # Cache should be updated
                import vulcanlab.config.app_config as app_config_module
                assert app_config_module._config_cache is config
                assert app_config_module._config_cache.database.host == "cached_host"

    def test_save_config_formats_json(self):
        """Test that save_config formats JSON with indentation."""
        config = AppConfig()
        
        with TemporaryDirectory() as tmpdir:
            config_file = Path(tmpdir) / "vulcanlab.config.json"
            
            with patch('vulcanlab.config.app_config.get_config_path') as mock_get_path:
                mock_get_path.return_value = config_file
                
                save_config(config)
                
                content = config_file.read_text(encoding='utf-8')
                # Should have indentation (pretty printed)
                assert "\n  " in content or "\n\t" in content

