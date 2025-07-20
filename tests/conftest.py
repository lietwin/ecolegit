import pytest
import tempfile
import json
import os
from pathlib import Path
from unittest.mock import MagicMock, patch
from fastapi.testclient import TestClient
import sys

# Add the parent directory to the path so we can import main
sys.path.insert(0, str(Path(__file__).parent.parent))

from main import app


@pytest.fixture
def client():
    """FastAPI test client"""
    return TestClient(app)


@pytest.fixture
def temp_config_file():
    """Create a temporary config file for testing"""
    with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as f:
        config = {
            "model_mappings": {
                "test-model": "test-model-v1",
                "gpt-4o": "gpt-4o-2024-05-13"
            },
            "security": {
                "enable_auth": False,
                "enable_webhook_signature": False,
                "max_tokens_per_request": 1000,
                "trusted_hosts": ["*"]
            },
            "rate_limiting": {
                "requests_per_minute": 100,
                "enabled": False
            }
        }
        json.dump(config, f)
        yield Path(f.name)
        # Cleanup
        os.unlink(f.name)


@pytest.fixture
def mock_ecologits():
    """Mock ecologits Impacts class"""
    with patch('main.Impacts') as mock_impacts_class:
        mock_impacts = MagicMock()
        mock_impacts.energy.value = 0.001234
        mock_impacts.gwp.value = 0.000567
        mock_impacts_class.from_model_and_tokens.return_value = mock_impacts
        yield mock_impacts_class


@pytest.fixture
def mock_models():
    """Mock the models repository"""
    mock_model = MagicMock()
    models_dict = {
        'gpt-4o-2024-05-13': mock_model,
        'claude-3-opus-20240229': mock_model,
        'test-model-v1': mock_model
    }
    with patch.dict('main.models', models_dict):
        yield models_dict


@pytest.fixture
def env_vars(monkeypatch):
    """Set up environment variables for testing"""
    monkeypatch.setenv("API_KEY", "test-api-key-12345")
    monkeypatch.setenv("WEBHOOK_SECRET", "test-webhook-secret-67890")
    monkeypatch.setenv("ENVIRONMENT", "test")
    monkeypatch.setenv("PORT", "8000")


@pytest.fixture
def auth_enabled_config():
    """Config with authentication enabled"""
    return {
        "model_mappings": {"gpt-4o": "gpt-4o-2024-05-13"},
        "security": {
            "enable_auth": True,
            "enable_webhook_signature": False,
            "max_tokens_per_request": 1000000,
            "trusted_hosts": ["*"]
        },
        "rate_limiting": {
            "requests_per_minute": 60,
            "enabled": True
        }
    }


@pytest.fixture
def webhook_signature_enabled_config():
    """Config with webhook signature verification enabled"""
    return {
        "model_mappings": {"gpt-4o": "gpt-4o-2024-05-13"},
        "security": {
            "enable_auth": False,
            "enable_webhook_signature": True,
            "max_tokens_per_request": 1000000,
            "trusted_hosts": ["*"]
        },
        "rate_limiting": {
            "requests_per_minute": 60,
            "enabled": False
        }
    }


@pytest.fixture
def sample_usage_request():
    """Sample valid usage request data"""
    return {
        "model": "gpt-4o",
        "input_tokens": 1000,
        "output_tokens": 500,
        "metadata": {"user_id": "test123", "session": "abc"}
    }


@pytest.fixture
def clean_config():
    """Clean up any config.json created during tests"""
    yield
    config_path = Path("config.json")
    if config_path.exists():
        config_path.unlink()