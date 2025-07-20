import pytest
import json
import tempfile
import os
from pathlib import Path
from unittest.mock import patch, mock_open
import sys

# Add the parent directory to the path so we can import main
sys.path.insert(0, str(Path(__file__).parent.parent))

from main import load_config


class TestConfigLoading:
    """Test configuration loading functionality"""

    def test_load_config_default_creation(self, clean_config):
        """Test that default config is created when file doesn't exist"""
        # Ensure no config file exists
        config_path = Path("config.json")
        if config_path.exists():
            config_path.unlink()
        
        config = load_config()
        
        # Check that config file was created
        assert config_path.exists()
        
        # Verify default values
        assert "model_mappings" in config
        assert "security" in config
        assert "rate_limiting" in config
        assert config["security"]["enable_auth"] is False
        assert config["rate_limiting"]["requests_per_minute"] == 60
        assert "gpt-4o" in config["model_mappings"]

    def test_load_config_file_exists(self, temp_config_file):
        """Test loading existing config file"""
        with patch('main.Path') as mock_path:
            mock_path.return_value.exists.return_value = True
            
            # Mock the file reading
            test_config = {
                "model_mappings": {"custom-model": "custom-model-v1"},
                "security": {"enable_auth": True},
                "rate_limiting": {"requests_per_minute": 120}
            }
            
            with patch('builtins.open', mock_open(read_data=json.dumps(test_config))):
                config = load_config()
            
            # Should merge with defaults
            assert config["model_mappings"]["custom-model"] == "custom-model-v1"
            assert config["security"]["enable_auth"] is True
            # Should have default values merged in
            assert "max_tokens_per_request" in config["security"]

    def test_load_config_merge_defaults(self):
        """Test that partial config gets merged with defaults"""
        partial_config = {
            "model_mappings": {"test-model": "test-v1"},
            "security": {"enable_auth": True}
            # Missing rate_limiting section
        }
        
        with patch('main.Path') as mock_path:
            mock_path.return_value.exists.return_value = True
            
            with patch('builtins.open', mock_open(read_data=json.dumps(partial_config))):
                config = load_config()
            
            # Should have partial config values
            assert config["model_mappings"]["test-model"] == "test-v1"
            assert config["security"]["enable_auth"] is True
            
            # Should have merged default values
            assert "rate_limiting" in config
            assert config["rate_limiting"]["requests_per_minute"] == 60

    def test_load_config_invalid_json(self, clean_config):
        """Test handling of malformed JSON"""
        with patch('main.Path') as mock_path:
            mock_path.return_value.exists.return_value = True
            
            # Invalid JSON
            with patch('builtins.open', mock_open(read_data='{"invalid": json}')):
                config = load_config()
            
            # Should fall back to defaults
            assert config["security"]["enable_auth"] is False
            assert config["rate_limiting"]["requests_per_minute"] == 60

    def test_load_config_file_permission_error(self, clean_config):
        """Test handling of file permission errors"""
        with patch('main.Path') as mock_path:
            mock_path.return_value.exists.return_value = True
            
            # Simulate permission error
            with patch('builtins.open', side_effect=PermissionError("Access denied")):
                config = load_config()
            
            # Should fall back to defaults
            assert config["security"]["enable_auth"] is False
            assert config["rate_limiting"]["requests_per_minute"] == 60

    def test_load_config_file_not_found_during_read(self, clean_config):
        """Test handling when file exists check passes but read fails"""
        with patch('main.Path') as mock_path:
            mock_path.return_value.exists.return_value = True
            
            # File disappeared between exists check and open
            with patch('builtins.open', side_effect=FileNotFoundError("File not found")):
                config = load_config()
            
            # Should fall back to defaults
            assert config["security"]["enable_auth"] is False

    def test_load_config_default_values_complete(self, clean_config):
        """Test that all expected default values are present"""
        config = load_config()
        
        # Check model mappings
        expected_models = [
            "gpt-4o", "gpt-4o-mini", "gpt-3.5-turbo", "gpt-4",
            "claude-3-opus", "claude-3-sonnet", "claude-3-haiku", 
            "claude-3-5-sonnet", "gemini-pro", "gemini-1.5-pro"
        ]
        for model in expected_models:
            assert model in config["model_mappings"]
        
        # Check security settings
        security = config["security"]
        assert security["enable_auth"] is False
        assert security["enable_webhook_signature"] is False
        assert security["max_tokens_per_request"] == 1000000
        assert security["trusted_hosts"] == ["*"]
        
        # Check rate limiting
        rate_limit = config["rate_limiting"]
        assert rate_limit["requests_per_minute"] == 60
        assert rate_limit["enabled"] is True