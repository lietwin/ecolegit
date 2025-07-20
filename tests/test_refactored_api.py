"""Integration tests for refactored API."""

import pytest
import json
import hashlib
import hmac
from fastapi.testclient import TestClient

from src.application import create_app


class TestRefactoredAPI:
    """Test the refactored API endpoints."""

    def test_health_endpoint(self, client):
        """Test health check endpoint."""
        response = client.get("/health")
        
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "healthy"
        assert data["service"] == "ecologits-webhook"
        assert "timestamp" in data

    def test_models_endpoint(self, client):
        """Test supported models endpoint."""
        response = client.get("/models")
        
        assert response.status_code == 200
        data = response.json()
        assert "supported_models" in data
        assert "total_ecologits_models" in data
        assert isinstance(data["supported_models"], list)

    def test_calculate_endpoint_success(self, client, sample_usage_request):
        """Test successful calculation request."""
        response = client.post("/calculate", json=sample_usage_request)
        
        assert response.status_code == 200
        data = response.json()
        
        assert data["model"] == "gpt-4o"
        assert data["input_tokens"] == 1000
        assert data["output_tokens"] == 500
        assert data["total_tokens"] == 1500
        assert data["energy_kwh"] == 0.001234
        assert data["gwp_kgco2eq"] == 0.000567
        assert data["success"] is True
        assert data["error"] is None
        assert data["calculation_id"].startswith("calc-")
        assert "timestamp" in data

    def test_calculate_endpoint_invalid_model(self, client):
        """Test calculation with invalid model name."""
        payload = {
            "model": "gpt-4o@invalid!",
            "input_tokens": 1000,
            "output_tokens": 500
        }
        
        response = client.post("/calculate", json=payload)
        assert response.status_code == 422

    def test_calculate_endpoint_negative_tokens(self, client):
        """Test calculation with negative tokens."""
        payload = {
            "model": "gpt-4o",
            "input_tokens": -100,
            "output_tokens": 500
        }
        
        response = client.post("/calculate", json=payload)
        assert response.status_code == 422

    def test_docs_available_in_test_environment(self, client):
        """Test that API docs are available in test environment."""
        response = client.get("/docs")
        assert response.status_code == 200