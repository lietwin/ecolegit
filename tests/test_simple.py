"""Simple tests for CI/CD validation."""

import pytest
import sys
from pathlib import Path

# Add the parent directory to the path
sys.path.insert(0, str(Path(__file__).parent.parent))


def test_imports():
    """Test that basic imports work."""
    from src.config.constants import Environment
    from src.config.settings import AppConfig
    from src.domain.models import UsageRequest, ImpactResponse
    
    assert Environment.PRODUCTION == "production"
    assert Environment.DEVELOPMENT == "development"
    assert Environment.TESTING == "testing"


def test_app_config_creation():
    """Test that AppConfig can be created."""
    from src.config.settings import AppConfig
    
    config = AppConfig()
    assert config.environment == "development"
    assert config.port == 8000
    assert "gpt-4o" in config.model_mappings


def test_usage_request_validation():
    """Test UsageRequest model validation."""
    from src.domain.models import UsageRequest
    
    # Valid request
    request = UsageRequest(
        model="gpt-4o",
        input_tokens=100,
        output_tokens=50
    )
    assert request.model == "gpt-4o"
    assert request.input_tokens == 100
    assert request.output_tokens == 50


def test_impact_response_creation():
    """Test ImpactResponse model creation."""
    from src.domain.models import ImpactResponse
    
    response = ImpactResponse(
        model="gpt-4o",
        input_tokens=100,
        output_tokens=50,
        total_tokens=150,
        energy_kwh=0.001,
        gwp_kgco2eq=0.0005,
        calculation_id="calc-123",
        timestamp="2024-01-01T00:00:00Z",
        success=True
    )
    assert response.model == "gpt-4o"
    assert response.success is True


def test_application_creation():
    """Test that application can be created."""
    from src.application import create_app
    
    # This will fail if there are import or configuration issues
    app = create_app()
    assert app is not None
    assert app.title == "EcoLogits Webhook"