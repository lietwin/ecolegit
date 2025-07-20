import pytest
import os
from unittest.mock import patch
from fastapi.testclient import TestClient
import sys
from pathlib import Path

# Add the parent directory to the path so we can import main
sys.path.insert(0, str(Path(__file__).parent.parent))

from main import app, CONFIG


class TestHealthEndpoint:
    """Test the /health endpoint"""

    def test_health_endpoint(self, client):
        """Test health check response"""
        response = client.get("/health")
        
        assert response.status_code == 200
        data = response.json()
        
        assert data["status"] == "healthy"
        assert data["service"] == "ecologits-webhook"
        assert "timestamp" in data

    def test_health_endpoint_timestamp_format(self, client):
        """Test that health endpoint timestamp is in correct format"""
        response = client.get("/health")
        
        assert response.status_code == 200
        data = response.json()
        
        # Check timestamp format (ISO 8601)
        timestamp = data["timestamp"]
        assert "T" in timestamp
        assert timestamp.endswith("Z") or "+" in timestamp or timestamp.count(":") >= 2

    def test_health_endpoint_no_auth_required(self, client):
        """Test that health endpoint doesn't require authentication"""
        with patch.dict(CONFIG, {"security": {"enable_auth": True}}):
            response = client.get("/health")
            
            assert response.status_code == 200


class TestModelsEndpoint:
    """Test the /models endpoint"""

    def test_models_endpoint(self, client, mock_models):
        """Test supported models listing"""
        response = client.get("/models")
        
        assert response.status_code == 200
        data = response.json()
        
        assert "supported_models" in data
        assert "total_ecologits_models" in data
        assert isinstance(data["supported_models"], list)
        assert isinstance(data["total_ecologits_models"], int)

    def test_models_endpoint_content(self, client):
        """Test that models endpoint returns expected model mappings"""
        response = client.get("/models")
        
        assert response.status_code == 200
        data = response.json()
        
        supported_models = data["supported_models"]
        
        # Check that default models are included
        expected_models = [
            "gpt-4o", "gpt-4o-mini", "gpt-3.5-turbo", "gpt-4",
            "claude-3-opus", "claude-3-sonnet", "claude-3-haiku",
            "claude-3-5-sonnet", "gemini-pro", "gemini-1.5-pro"
        ]
        
        for model in expected_models:
            assert model in supported_models

    def test_models_endpoint_no_auth_required(self, client):
        """Test that models endpoint doesn't require authentication"""
        with patch.dict(CONFIG, {"security": {"enable_auth": True}}):
            response = client.get("/models")
            
            assert response.status_code == 200

    def test_models_endpoint_ecologits_count(self, client, mock_models):
        """Test that ecologits model count is returned"""
        response = client.get("/models")
        
        assert response.status_code == 200
        data = response.json()
        
        # Should return the count of models in the mocked ecologits models dict
        assert data["total_ecologits_models"] == len(mock_models)


class TestTestEndpoint:
    """Test the /test endpoint (development only)"""

    def test_test_endpoint_development(self, client, mock_models, mock_ecologits):
        """Test that test endpoint works in development environment"""
        with patch.dict(os.environ, {"ENVIRONMENT": "development"}):
            response = client.get("/test")
            
            assert response.status_code == 200
            data = response.json()
            
            assert data["test_model"] == "gpt-4o"
            assert data["test_tokens"] == "1000 input + 500 output"
            assert data["energy_kwh"] == 0.001234
            assert data["gwp_kgco2eq"] == 0.000567
            assert data["success"] is True
            assert data["environment"] == "development"

    def test_test_endpoint_production_disabled(self, client):
        """Test that test endpoint is disabled in production"""
        with patch.dict(os.environ, {"ENVIRONMENT": "production"}):
            response = client.get("/test")
            
            assert response.status_code == 404

    def test_test_endpoint_default_environment(self, client, mock_models, mock_ecologits):
        """Test test endpoint when ENVIRONMENT is not set (defaults to development)"""
        with patch.dict(os.environ, {}, clear=True):
            response = client.get("/test")
            
            # Should work since default is not production
            assert response.status_code == 200

    def test_test_endpoint_calculation_values(self, client, mock_models, mock_ecologits):
        """Test that test endpoint returns expected calculation values"""
        with patch.dict(os.environ, {"ENVIRONMENT": "test"}):
            response = client.get("/test")
            
            assert response.status_code == 200
            data = response.json()
            
            # Verify the test uses specific hardcoded values
            assert data["test_model"] == "gpt-4o"
            assert "1000 input" in data["test_tokens"]
            assert "500 output" in data["test_tokens"]
            assert isinstance(data["energy_kwh"], (int, float))
            assert isinstance(data["gwp_kgco2eq"], (int, float))

    def test_test_endpoint_calculation_error(self, client, mock_models):
        """Test test endpoint when calculation fails"""
        with patch.dict(os.environ, {"ENVIRONMENT": "development"}):
            with patch('main.calculate_impact') as mock_calculate:
                mock_calculate.return_value = {
                    'energy_kwh': 0,
                    'gwp_kgco2eq': 0,
                    'success': False,
                    'error': 'Test error'
                }
                
                response = client.get("/test")
                
                assert response.status_code == 200
                data = response.json()
                
                assert data["success"] is False
                assert data["energy_kwh"] == 0
                assert data["gwp_kgco2eq"] == 0

    def test_test_endpoint_no_auth_required(self, client, mock_models, mock_ecologits):
        """Test that test endpoint doesn't require authentication"""
        with patch.dict(os.environ, {"ENVIRONMENT": "development"}):
            with patch.dict(CONFIG, {"security": {"enable_auth": True}}):
                response = client.get("/test")
                
                assert response.status_code == 200


class TestDocsEndpoints:
    """Test documentation endpoint access control"""

    def test_docs_development_accessible(self, client):
        """Test that docs are accessible in development"""
        with patch.dict(os.environ, {"ENVIRONMENT": "development"}):
            response = client.get("/docs")
            
            # Should either return docs or redirect to docs
            assert response.status_code in [200, 307]

    def test_docs_production_disabled(self, client):
        """Test that docs are disabled in production"""
        with patch.dict(os.environ, {"ENVIRONMENT": "production"}):
            response = client.get("/docs")
            
            assert response.status_code == 404

    def test_redoc_development_accessible(self, client):
        """Test that redoc is accessible in development"""
        with patch.dict(os.environ, {"ENVIRONMENT": "development"}):
            response = client.get("/redoc")
            
            # Should either return redoc or redirect to redoc
            assert response.status_code in [200, 307]

    def test_redoc_production_disabled(self, client):
        """Test that redoc is disabled in production"""
        with patch.dict(os.environ, {"ENVIRONMENT": "production"}):
            response = client.get("/redoc")
            
            assert response.status_code == 404