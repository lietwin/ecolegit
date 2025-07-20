"""Test configuration for refactored clean architecture."""

import pytest
import tempfile
import json
import os
from pathlib import Path
from unittest.mock import MagicMock, patch
from fastapi.testclient import TestClient

from src.application import create_app
from src.config.settings import AppConfig, SecurityConfig, RateLimitConfig
from src.domain.services import EcologitsRepository


@pytest.fixture
def app_config():
    """Provide test configuration."""
    return AppConfig(
        model_mappings={"gpt-4o": "gpt-4o-2024-05-13", "test-model": "test-model-v1"},
        security=SecurityConfig(
            enable_auth=False,
            enable_webhook_signature=False,
            max_tokens_per_request=1000,
            trusted_hosts=["*"]
        ),
        rate_limiting=RateLimitConfig(
            requests_per_minute=100,
            enabled=False
        ),
        api_key="test-api-key",
        webhook_secret="test-webhook-secret"
    )


@pytest.fixture
def mock_ecologits_repo():
    """Mock EcologitsRepository."""
    repo = MagicMock(spec=EcologitsRepository)
    
    # Mock impacts object
    mock_impacts = MagicMock()
    mock_impacts.energy.value = 0.001234
    mock_impacts.gwp.value = 0.000567
    
    # Mock model
    mock_model = MagicMock()
    
    # Setup repository methods
    repo.get_model.return_value = mock_model
    repo.calculate_impacts.return_value = mock_impacts
    repo.get_available_models.return_value = {
        'gpt-4o-2024-05-13': mock_model,
        'test-model-v1': mock_model
    }
# repo.is_model_supported.return_value = True  # Not needed for basic tests
    
    return repo


@pytest.fixture
def client(app_config, mock_ecologits_repo):
    """FastAPI test client with mocked dependencies."""
    with patch('src.infrastructure.ecologits_adapter.EcologitsAdapter') as mock_adapter_class:
        mock_adapter_class.return_value = mock_ecologits_repo
        
        with patch('src.config.settings.ConfigLoader') as mock_config_loader:
            mock_config_loader.return_value.load.return_value = app_config
            
            app = create_app()
            return TestClient(app)


@pytest.fixture
def temp_config_file():
    """Create a temporary config file for testing."""
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
        os.unlink(f.name)


@pytest.fixture
def env_vars(monkeypatch):
    """Set up environment variables for testing."""
    monkeypatch.setenv("API_KEY", "test-api-key-12345")
    monkeypatch.setenv("WEBHOOK_SECRET", "test-webhook-secret-67890")
    monkeypatch.setenv("ENVIRONMENT", "testing")
    monkeypatch.setenv("PORT", "8000")


@pytest.fixture
def sample_usage_request():
    """Sample valid usage request data."""
    return {
        "model": "gpt-4o",
        "input_tokens": 1000,
        "output_tokens": 500,
        "metadata": {"user_id": "test123", "session": "abc"}
    }