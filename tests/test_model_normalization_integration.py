"""Integration tests for model normalization in the API."""

import pytest
from fastapi.testclient import TestClient
import sys
from pathlib import Path

# Add the parent directory to the path
sys.path.insert(0, str(Path(__file__).parent.parent))

from src.application import create_app
from .conftest import app_config, mock_ecologits_repo


@pytest.fixture  
def client(app_config, mock_ecologits_repo):
    """Create test client with mocked dependencies."""
    from unittest.mock import patch
    
    with patch('src.infrastructure.ecologits_adapter.EcologitsAdapter') as mock_adapter_class:
        mock_adapter_class.return_value = mock_ecologits_repo
        
        with patch('src.config.settings.ConfigLoader') as mock_config_loader:
            mock_config_loader.return_value.load.return_value = app_config
            
            app = create_app()
            return TestClient(app)


class TestModelNormalizationIntegration:
    """Test model normalization through the actual API endpoints."""
    
    def test_calculate_endpoint_handles_gpt4o_typo(self, client):
        """Test that gpt4o (missing hyphen) works in calculation endpoint."""
        response = client.post("/calculate", json={
            "model": "gpt4o",
            "input_tokens": 1000,
            "output_tokens": 500
        })
        
        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True
        assert data["model"] == "gpt4o"  # Original input preserved in response
        assert data["energy_kwh"] > 0
        assert data["gwp_kgco2eq"] > 0
        assert "calculation_id" in data
    
    def test_calculate_endpoint_handles_claudeopus_typo(self, client):
        """Test that claudeopus (missing hyphens) works in calculation endpoint."""
        response = client.post("/calculate", json={
            "model": "claudeopus",
            "input_tokens": 1000,
            "output_tokens": 500
        })
        
        assert response.status_code == 200
        data = response.json()
        print(f"DEBUG: Response data for claudeopus: {data}")  # Debug output
        assert data["success"] is True
        assert data["model"] == "claudeopus"
        assert data["energy_kwh"] > 0
        assert data["gwp_kgco2eq"] > 0
    
    def test_calculate_endpoint_handles_gpt4omini_typo(self, client):
        """Test that gpt4omini (missing hyphens) works in calculation endpoint."""
        response = client.post("/calculate", json={
            "model": "gpt4omini",
            "input_tokens": 1000,
            "output_tokens": 500
        })
        
        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True
        assert data["energy_kwh"] > 0
        assert data["gwp_kgco2eq"] > 0
    
    def test_calculate_endpoint_handles_claude35sonnet_typo(self, client):
        """Test that claude35sonnet (missing hyphens) works in calculation endpoint."""
        response = client.post("/calculate", json={
            "model": "claude35sonnet", 
            "input_tokens": 1000,
            "output_tokens": 500
        })
        
        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True
        assert data["energy_kwh"] > 0
        assert data["gwp_kgco2eq"] > 0
    
    def test_calculate_endpoint_handles_geminipro_typo(self, client):
        """Test that geminipro (missing hyphen) works in calculation endpoint."""
        response = client.post("/calculate", json={
            "model": "geminipro",
            "input_tokens": 1000,
            "output_tokens": 500
        })
        
        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True
        assert data["energy_kwh"] > 0
        assert data["gwp_kgco2eq"] > 0
    
    def test_calculate_endpoint_provides_suggestions_for_unknown_model(self, client):
        """Test that unknown models get helpful error messages with suggestions."""
        response = client.post("/calculate", json={
            "model": "definitely-not-a-real-model-xyz",  # Definitely non-existent 
            "input_tokens": 1000,
            "output_tokens": 500
        })
        
        assert response.status_code == 200
        data = response.json()
        assert data["success"] is False
        assert ("not supported" in data["error"] or "not found" in data["error"])  # Should show error
        assert data["energy_kwh"] == 0
        assert data["gwp_kgco2eq"] == 0
    
    def test_calculate_endpoint_preserves_exact_matches(self, client):
        """Test that exact model names still work (backward compatibility)."""
        response = client.post("/calculate", json={
            "model": "gpt-4o",  # Exact name from config
            "input_tokens": 1000,
            "output_tokens": 500
        })
        
        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True
        assert data["model"] == "gpt-4o"
        assert data["energy_kwh"] > 0
    
    def test_multiple_typo_variations_work(self, client):
        """Test multiple variations of the same model work."""
        variations = ["gpt4o", "gpt-4o", "GPT4O", "GPT-4O"]
        
        for model_name in variations:
            response = client.post("/calculate", json={
                "model": model_name,
                "input_tokens": 100,
                "output_tokens": 50
            })
            
            assert response.status_code == 200
            data = response.json()
            assert data["success"] is True, f"Failed for model: {model_name}"
            assert data["energy_kwh"] > 0, f"No energy calculated for: {model_name}"
    
    def test_claude_variations_work(self, client):
        """Test multiple Claude model variations work."""
        variations = [
            "claudeopus", "claude3opus", "claude-3opus",
            "claudesonnet", "claude3sonnet", "claude-3sonnet"
        ]
        
        for model_name in variations:
            response = client.post("/calculate", json={
                "model": model_name,
                "input_tokens": 100,
                "output_tokens": 50
            })
            
            assert response.status_code == 200
            data = response.json()
            assert data["success"] is True, f"Failed for model: {model_name}"
            assert data["energy_kwh"] > 0, f"No energy calculated for: {model_name}"
    
    def test_case_insensitive_normalization(self, client):
        """Test that model names are case insensitive."""
        response = client.post("/calculate", json={
            "model": "GPT4O",  # Uppercase
            "input_tokens": 1000,
            "output_tokens": 500
        })
        
        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True
        assert data["energy_kwh"] > 0
    
    def test_whitespace_handling(self, client):
        """Test that leading/trailing whitespace in model names is rejected with helpful error."""
        response = client.post("/calculate", json={
            "model": " gpt4o ",  # With spaces
            "input_tokens": 1000,
            "output_tokens": 500
        })
        
        # Should be rejected at validation level
        assert response.status_code == 422
        error_data = response.json()
        assert "detail" in error_data
        assert "Model name contains invalid characters" in str(error_data)