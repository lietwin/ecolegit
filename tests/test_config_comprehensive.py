"""Comprehensive tests for configuration management."""

import pytest
import json
import tempfile
import os
from pathlib import Path
from unittest.mock import Mock, patch, mock_open
from src.config.settings import AppConfig, ConfigLoader, ConfigurationError, SecurityConfig, RateLimitConfig, CORSConfig
from src.config.constants import Environment, DefaultValues, ModelMappings


class TestSecurityConfig:
    """Test SecurityConfig dataclass."""
    
    def test_security_config_defaults(self):
        """Test SecurityConfig default values."""
        config = SecurityConfig()
        
        assert config.enable_auth is False
        assert config.enable_webhook_signature is False
        assert config.max_tokens_per_request == 1000000
        assert config.trusted_hosts == ["*"]
    
    def test_security_config_custom(self):
        """Test SecurityConfig with custom values."""
        config = SecurityConfig(
            enable_auth=True,
            enable_webhook_signature=True,
            max_tokens_per_request=500000,
            trusted_hosts=["localhost", "127.0.0.1"]
        )
        
        assert config.enable_auth is True
        assert config.enable_webhook_signature is True
        assert config.max_tokens_per_request == 500000
        assert config.trusted_hosts == ["localhost", "127.0.0.1"]


class TestRateLimitConfig:
    """Test RateLimitConfig dataclass."""
    
    def test_rate_limit_config_defaults(self):
        """Test RateLimitConfig default values."""
        config = RateLimitConfig()
        
        assert config.requests_per_minute == 60
        assert config.enabled is True
    
    def test_rate_limit_config_custom(self):
        """Test RateLimitConfig with custom values."""
        config = RateLimitConfig(
            requests_per_minute=120,
            enabled=False
        )
        
        assert config.requests_per_minute == 120
        assert config.enabled is False


class TestCORSConfig:
    """Test CORSConfig dataclass."""
    
    def test_cors_config_defaults(self):
        """Test CORSConfig default values."""
        config = CORSConfig()
        
        assert "https://hook.eu1.make.com" in config.allowed_origins
        assert "https://hook.us1.make.com" in config.allowed_origins
        assert "POST" in config.allowed_methods
        assert "Content-Type" in config.allowed_headers
        assert config.allow_credentials is False


class TestAppConfig:
    """Test AppConfig dataclass."""
    
    def test_app_config_defaults(self):
        """Test AppConfig default values."""
        config = AppConfig()
        
        assert isinstance(config.model_mappings, dict)
        assert isinstance(config.security, SecurityConfig)
        assert isinstance(config.rate_limiting, RateLimitConfig)
        assert isinstance(config.cors, CORSConfig)
        assert config.environment == Environment.DEVELOPMENT
        assert config.port == 8000
        assert config.api_key is None
        assert config.webhook_secret is None
    
    def test_app_config_from_dict_minimal(self):
        """Test AppConfig.from_dict with minimal data."""
        config_dict = {}
        config = AppConfig.from_dict(config_dict)
        
        assert isinstance(config, AppConfig)
        assert config.environment == Environment.DEVELOPMENT
        assert config.security.enable_auth is False
    
    def test_app_config_from_dict_complete(self):
        """Test AppConfig.from_dict with complete data."""
        config_dict = {
            "model_mappings": {"gpt-4": "gpt-4-0613"},
            "security": {
                "enable_auth": True,
                "enable_webhook_signature": True,
                "max_tokens_per_request": 100000,
                "trusted_hosts": ["localhost"]
            },
            "rate_limiting": {
                "requests_per_minute": 30,
                "enabled": False
            }
        }
        
        with patch.dict(os.environ, {"ENVIRONMENT": "production", "PORT": "9000", "API_KEY": "test-key"}):
            config = AppConfig.from_dict(config_dict)
        
        assert config.model_mappings == {"gpt-4": "gpt-4-0613"}
        assert config.security.enable_auth is True
        assert config.security.max_tokens_per_request == 100000
        assert config.rate_limiting.requests_per_minute == 30
        assert config.rate_limiting.enabled is False
        assert config.environment == Environment.PRODUCTION
        assert config.port == 9000
        assert config.api_key == "test-key"
    
    def test_app_config_to_dict(self):
        """Test AppConfig.to_dict serialization."""
        config = AppConfig()
        config_dict = config.to_dict()
        
        assert "model_mappings" in config_dict
        assert "security" in config_dict
        assert "rate_limiting" in config_dict
        
        # Check nested structure
        assert "enable_auth" in config_dict["security"]
        assert "requests_per_minute" in config_dict["rate_limiting"]
    
    @patch.dict(os.environ, {"ENVIRONMENT": "invalid_env"})
    def test_app_config_invalid_environment(self):
        """Test AppConfig with invalid environment variable."""
        # Should handle invalid environment gracefully
        config = AppConfig.from_dict({})
        # Environment should default or handle the invalid value
        assert config.environment in [Environment.DEVELOPMENT, Environment.TESTING, Environment.PRODUCTION]


class TestConfigLoader:
    """Test ConfigLoader class."""
    
    def test_config_loader_init(self):
        """Test ConfigLoader initialization."""
        loader = ConfigLoader("test_config.json")
        
        assert loader.config_file == Path("test_config.json")
    
    def test_config_loader_default_file(self):
        """Test ConfigLoader with default file."""
        loader = ConfigLoader()
        
        assert loader.config_file == Path(DefaultValues.DEFAULT_CONFIG_FILE)
    
    def test_load_existing_file_success(self):
        """Test loading existing valid config file."""
        config_data = {
            "model_mappings": {"gpt-4": "gpt-4-0613"},
            "security": {"enable_auth": True}
        }
        
        with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as f:
            json.dump(config_data, f)
            temp_path = f.name
        
        try:
            loader = ConfigLoader(temp_path)
            config = loader.load()
            
            assert isinstance(config, AppConfig)
            assert config.model_mappings["gpt-4"] == "gpt-4-0613"
            assert config.security.enable_auth is True
        finally:
            os.unlink(temp_path)
    
    def test_load_nonexistent_file_creates_default(self):
        """Test loading non-existent file creates default config."""
        with tempfile.TemporaryDirectory() as temp_dir:
            config_path = os.path.join(temp_dir, "nonexistent_config.json")
            loader = ConfigLoader(config_path)
            
            config = loader.load()
            
            assert isinstance(config, AppConfig)
            assert Path(config_path).exists()  # Should have created the file
    
    def test_load_invalid_json_fallback(self):
        """Test loading invalid JSON falls back to default."""
        with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as f:
            f.write("{ invalid json }")
            temp_path = f.name
        
        try:
            loader = ConfigLoader(temp_path)
            config = loader.load()
            
            assert isinstance(config, AppConfig)
            # Should have default values
            assert config.environment == Environment.DEVELOPMENT
        finally:
            os.unlink(temp_path)
    
    def test_load_file_read_error_fallback(self):
        """Test file read error falls back to default."""
        # Create a file that will cause read error
        with tempfile.NamedTemporaryFile(delete=False) as f:
            temp_path = f.name
        
        # Make file unreadable
        os.chmod(temp_path, 0o000)
        
        try:
            loader = ConfigLoader(temp_path)
            config = loader.load()
            
            assert isinstance(config, AppConfig)
        finally:
            os.chmod(temp_path, 0o644)  # Restore permissions
            os.unlink(temp_path)
    
    def test_load_json_decode_error(self):
        """Test JSON decode error handling."""
        with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as f:
            f.write('{"key": invalid}')  # Invalid JSON
            temp_path = f.name
        
        try:
            loader = ConfigLoader(temp_path)
            
            with patch('src.config.settings.logger') as mock_logger:
                config = loader.load()
                
                assert isinstance(config, AppConfig)
                mock_logger.warning.assert_called()
        finally:
            os.unlink(temp_path)
    
    def test_save_config_success(self):
        """Test successful config saving."""
        config = AppConfig()
        
        with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as f:
            temp_path = f.name
        
        try:
            loader = ConfigLoader(temp_path)
            loader.save(config)
            
            # Verify file was created and contains valid JSON
            with open(temp_path, 'r') as f:
                saved_data = json.load(f)
            
            assert "model_mappings" in saved_data
            assert "security" in saved_data
        finally:
            os.unlink(temp_path)
    
    def test_save_config_error(self):
        """Test config save error handling."""
        config = AppConfig()
        
        # Try to save to an invalid path
        invalid_path = "/root/invalid/path/config.json"
        loader = ConfigLoader(invalid_path)
        
        with pytest.raises(ConfigurationError):
            loader.save(config)
    
    def test_create_default_config_directory_creation(self):
        """Test default config creation with directory creation."""
        with tempfile.TemporaryDirectory() as temp_dir:
            config_path = os.path.join(temp_dir, "subdir", "config.json")
            loader = ConfigLoader(config_path)
            
            # Directory doesn't exist yet
            assert not os.path.exists(os.path.dirname(config_path))
            
            config = loader._create_default_config()
            
            assert isinstance(config, AppConfig)
            # Note: Directory might not be created until save() is called
    
    def test_create_default_config_write_error(self):
        """Test default config creation with write error."""
        # Create a directory where file should be (will cause write error)
        with tempfile.TemporaryDirectory() as temp_dir:
            config_path = os.path.join(temp_dir, "is_directory")
            os.makedirs(config_path)  # Create directory with same name as file
            
            loader = ConfigLoader(config_path)
            
            with patch('src.config.settings.logger') as mock_logger:
                config = loader._create_default_config()
                
                assert isinstance(config, AppConfig)
                mock_logger.warning.assert_called()


class TestConfigurationError:
    """Test ConfigurationError exception."""
    
    def test_configuration_error_creation(self):
        """Test ConfigurationError creation."""
        error = ConfigurationError("Test error")
        
        assert str(error) == "Test error"
        assert isinstance(error, Exception)
    
    def test_configuration_error_inheritance(self):
        """Test ConfigurationError inheritance."""
        assert issubclass(ConfigurationError, Exception)


class TestConfigurationEdgeCases:
    """Test edge cases and error scenarios."""
    
    def test_empty_config_file(self):
        """Test handling of empty config file."""
        with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as f:
            # Write empty file
            temp_path = f.name
        
        try:
            loader = ConfigLoader(temp_path)
            config = loader.load()
            
            assert isinstance(config, AppConfig)
        finally:
            os.unlink(temp_path)
    
    def test_config_with_null_values(self):
        """Test config with null/None values."""
        config_data = {
            "model_mappings": None,
            "security": None
        }
        
        with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as f:
            json.dump(config_data, f)
            temp_path = f.name
        
        try:
            loader = ConfigLoader(temp_path)
            config = loader.load()
            
            assert isinstance(config, AppConfig)
            # Should handle None values gracefully
        finally:
            os.unlink(temp_path)
    
    def test_config_with_extra_fields(self):
        """Test config with extra unknown fields."""
        config_data = {
            "model_mappings": {"gpt-4": "gpt-4-0613"},
            "unknown_field": "should_be_ignored",
            "another_unknown": {"nested": "value"}
        }
        
        with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as f:
            json.dump(config_data, f)
            temp_path = f.name
        
        try:
            loader = ConfigLoader(temp_path)
            config = loader.load()
            
            assert isinstance(config, AppConfig)
            assert config.model_mappings["gpt-4"] == "gpt-4-0613"
            # Extra fields should be ignored
        finally:
            os.unlink(temp_path)
    
    @patch('src.config.settings.json.load')
    def test_load_general_exception(self, mock_json_load):
        """Test general exception handling in load."""
        mock_json_load.side_effect = Exception("Unexpected error")
        
        with tempfile.NamedTemporaryFile(suffix='.json') as f:
            loader = ConfigLoader(f.name)
            
            with pytest.raises(ConfigurationError):
                loader.load()
    
    @patch('src.config.settings.json.dump')
    def test_save_json_error(self, mock_json_dump):
        """Test JSON serialization error in save."""
        mock_json_dump.side_effect = TypeError("Not serializable")
        
        config = AppConfig()
        
        with tempfile.NamedTemporaryFile(suffix='.json') as f:
            loader = ConfigLoader(f.name)
            
            with pytest.raises(ConfigurationError):
                loader.save(config)


class TestEnvironmentVariableHandling:
    """Test environment variable handling in configuration."""
    
    @patch.dict(os.environ, {})
    def test_missing_environment_variables(self):
        """Test handling of missing environment variables."""
        config = AppConfig.from_dict({})
        
        assert config.environment == Environment.DEVELOPMENT  # Default
        assert config.port == DefaultValues.DEFAULT_PORT  # Default
        assert config.api_key is None
        assert config.webhook_secret is None
    
    @patch.dict(os.environ, {
        "ENVIRONMENT": "production",
        "PORT": "3000",
        "API_KEY": "secret-key",
        "WEBHOOK_SECRET": "webhook-secret"
    })
    def test_all_environment_variables_set(self):
        """Test with all environment variables set."""
        config = AppConfig.from_dict({})
        
        assert config.environment == Environment.PRODUCTION
        assert config.port == 3000
        assert config.api_key == "secret-key"
        assert config.webhook_secret == "webhook-secret"
    
    @patch.dict(os.environ, {"PORT": "not_a_number"})
    def test_invalid_port_environment_variable(self):
        """Test handling of invalid PORT environment variable."""
        with pytest.raises(ValueError):
            AppConfig.from_dict({})


class TestModelMappingsHandling:
    """Test model mappings configuration handling."""
    
    def test_default_model_mappings(self):
        """Test default model mappings are loaded."""
        config = AppConfig()
        
        # Should have default mappings
        assert len(config.model_mappings) > 0
        # Should be a copy, not the original
        assert config.model_mappings is not ModelMappings.DEFAULT_MAPPINGS
    
    def test_custom_model_mappings_override(self):
        """Test custom model mappings override defaults."""
        custom_mappings = {"custom-model": "custom-target"}
        config_dict = {"model_mappings": custom_mappings}
        
        config = AppConfig.from_dict(config_dict)
        
        assert config.model_mappings == custom_mappings
    
    def test_empty_model_mappings(self):
        """Test handling of empty model mappings."""
        config_dict = {"model_mappings": {}}
        
        config = AppConfig.from_dict(config_dict)
        
        assert config.model_mappings == {}


class TestConfigIntegration:
    """Integration tests for configuration system."""
    
    def test_full_config_lifecycle(self):
        """Test complete config lifecycle: create, save, load, modify."""
        with tempfile.TemporaryDirectory() as temp_dir:
            config_path = os.path.join(temp_dir, "test_config.json")
            loader = ConfigLoader(config_path)
            
            # 1. Create default config
            config1 = loader.load()
            assert isinstance(config1, AppConfig)
            
            # 2. Modify config
            config1.security.enable_auth = True
            config1.model_mappings["test"] = "test-model"
            
            # 3. Save config
            loader.save(config1)
            
            # 4. Load again and verify changes persisted
            config2 = loader.load()
            assert config2.security.enable_auth is True
            assert config2.model_mappings["test"] == "test-model"