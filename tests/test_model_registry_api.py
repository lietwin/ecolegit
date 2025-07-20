"""Tests for model registry API endpoints."""

import pytest
from unittest.mock import Mock, patch
from fastapi.testclient import TestClient
from src.application import create_app
from src.domain.model_discovery import ModelMatch, ModelInfo


@pytest.fixture
def app():
    """Create test FastAPI app."""
    return create_app()


@pytest.fixture
def client(app):
    """Create test client."""
    return TestClient(app)


@pytest.fixture
def mock_model_discovery_service():
    """Create mock ModelDiscoveryService."""
    mock_service = Mock()
    
    # Mock supported models
    mock_service.get_supported_models.return_value = [
        "gpt-4o", "gpt-4o-mini", "gpt-3.5-turbo",
        "claude-3-opus", "claude-3-sonnet", "gemini-1.5-pro"
    ]
    
    # Mock models by provider
    mock_service.get_models_by_provider.return_value = {
        "openai": ["gpt-3.5-turbo", "gpt-4o", "gpt-4o-mini"],
        "anthropic": ["claude-3-opus", "claude-3-sonnet"],
        "google": ["gemini-1.5-pro"]
    }
    
    # Mock search results
    mock_service.search_models.return_value = [
        ("gpt-4o", 0.95),
        ("gpt-4o-mini", 0.85),
        ("gpt-3.5-turbo", 0.75)
    ]
    
    # Mock best match
    mock_service.find_best_match.return_value = ModelMatch(
        matched_name="gpt-4o",
        original_name="gpt4o",
        confidence=0.95,
        match_type="alias"
    )
    
    # Mock refresh cache
    mock_service.refresh_cache.return_value = {
        "gpt-4o": ModelInfo("gpt-4o", "openai", True, ["gpt4o"]),
        "claude-3-opus": ModelInfo("claude-3-opus", "anthropic", True, ["claude3opus"])
    }
    
    return mock_service


class TestSupportedModelsEndpoint:
    """Test /api/models/supported endpoint."""
    
    @patch('src.api.dependencies.get_model_discovery_service')
    def test_get_supported_models_success(self, mock_get_service, client, mock_model_discovery_service):
        """Test successful retrieval of supported models."""
        mock_get_service.return_value = mock_model_discovery_service
        
        response = client.get("/api/models/supported")
        
        assert response.status_code == 200
        data = response.json()
        
        assert "models" in data
        assert "total_count" in data
        assert "by_provider" in data
        
        assert len(data["models"]) == 6
        assert data["total_count"] == 6
        assert "gpt-4o" in data["models"]
        assert "claude-3-opus" in data["models"]
        
        # Check provider grouping
        assert "openai" in data["by_provider"]
        assert "anthropic" in data["by_provider"]
        assert len(data["by_provider"]["openai"]) == 3
    
    @patch('src.api.dependencies.get_model_discovery_service')
    def test_get_supported_models_service_error(self, mock_get_service, client):
        """Test error handling when service fails."""
        mock_service = Mock()
        mock_service.get_supported_models.side_effect = Exception("Service error")
        mock_get_service.return_value = mock_service
        
        response = client.get("/api/models/supported")
        
        assert response.status_code == 500
        assert "Failed to retrieve supported models" in response.json()["detail"]


class TestSearchModelsEndpoint:
    """Test /api/models/search endpoint."""
    
    @patch('src.api.dependencies.get_model_discovery_service')
    def test_search_models_success(self, mock_get_service, client, mock_model_discovery_service):
        """Test successful model search."""
        mock_get_service.return_value = mock_model_discovery_service
        
        response = client.get("/api/models/search?q=gpt&limit=3")
        
        assert response.status_code == 200
        data = response.json()
        
        assert isinstance(data, list)
        assert len(data) == 3
        
        # Check result structure
        for result in data:
            assert "name" in result
            assert "confidence" in result
            assert isinstance(result["confidence"], float)
        
        mock_model_discovery_service.search_models.assert_called_once_with("gpt", 3)
    
    @patch('src.api.dependencies.get_model_discovery_service')
    def test_search_models_default_limit(self, mock_get_service, client, mock_model_discovery_service):
        """Test search with default limit."""
        mock_get_service.return_value = mock_model_discovery_service
        
        response = client.get("/api/models/search?q=claude")
        
        assert response.status_code == 200
        mock_model_discovery_service.search_models.assert_called_once_with("claude", 10)
    
    @patch('src.api.dependencies.get_model_discovery_service')
    def test_search_models_limit_validation(self, mock_get_service, client, mock_model_discovery_service):
        """Test search limit validation."""
        mock_get_service.return_value = mock_model_discovery_service
        
        # Test limit too high
        response = client.get("/api/models/search?q=test&limit=100")
        assert response.status_code == 422
        
        # Test limit too low
        response = client.get("/api/models/search?q=test&limit=0")
        assert response.status_code == 422
    
    @patch('src.api.dependencies.get_model_discovery_service')
    def test_search_models_missing_query(self, mock_get_service, client, mock_model_discovery_service):
        """Test search without query parameter."""
        mock_get_service.return_value = mock_model_discovery_service
        
        response = client.get("/api/models/search")
        
        assert response.status_code == 422
    
    @patch('src.api.dependencies.get_model_discovery_service')
    def test_search_models_service_error(self, mock_get_service, client):
        """Test error handling when search service fails."""
        mock_service = Mock()
        mock_service.search_models.side_effect = Exception("Search failed")
        mock_get_service.return_value = mock_service
        
        response = client.get("/api/models/search?q=test")
        
        assert response.status_code == 500
        assert "Failed to search models" in response.json()["detail"]


class TestMatchModelEndpoint:
    """Test /api/models/match endpoint."""
    
    @patch('src.api.dependencies.get_model_discovery_service')
    def test_match_model_success(self, mock_get_service, client, mock_model_discovery_service):
        """Test successful model matching."""
        mock_get_service.return_value = mock_model_discovery_service
        
        response = client.get("/api/models/match?name=gpt4o")
        
        assert response.status_code == 200
        data = response.json()
        
        assert data["matched_name"] == "gpt-4o"
        assert data["original_name"] == "gpt4o"
        assert data["confidence"] == 0.95
        assert data["match_type"] == "alias"
        assert data["available"] is True
        
        mock_model_discovery_service.find_best_match.assert_called_once_with("gpt4o")
    
    @patch('src.api.dependencies.get_model_discovery_service')
    def test_match_model_not_found(self, mock_get_service, client):
        """Test model matching when no match found."""
        mock_service = Mock()
        mock_service.find_best_match.return_value = None
        mock_get_service.return_value = mock_service
        
        response = client.get("/api/models/match?name=unknown-model")
        
        assert response.status_code == 404
        detail = response.json()["detail"]
        assert "No suitable model found for 'unknown-model'" in detail
        assert "/models/search" in detail
    
    @patch('src.api.dependencies.get_model_discovery_service')
    def test_match_model_missing_name(self, mock_get_service, client, mock_model_discovery_service):
        """Test match without name parameter."""
        mock_get_service.return_value = mock_model_discovery_service
        
        response = client.get("/api/models/match")
        
        assert response.status_code == 422
    
    @patch('src.api.dependencies.get_model_discovery_service')
    def test_match_model_service_error(self, mock_get_service, client):
        """Test error handling when match service fails."""
        mock_service = Mock()
        mock_service.find_best_match.side_effect = Exception("Match failed")
        mock_get_service.return_value = mock_service
        
        response = client.get("/api/models/match?name=test")
        
        assert response.status_code == 500
        assert "Failed to match model" in response.json()["detail"]


class TestRefreshCacheEndpoint:
    """Test /api/models/refresh endpoint."""
    
    @patch('src.api.dependencies.get_model_discovery_service')
    def test_refresh_cache_success(self, mock_get_service, client, mock_model_discovery_service):
        """Test successful cache refresh."""
        mock_get_service.return_value = mock_model_discovery_service
        
        response = client.post("/api/models/refresh")
        
        assert response.status_code == 200
        data = response.json()
        
        assert "message" in data
        assert "discovered_models" in data
        assert "models" in data
        
        assert data["discovered_models"] == 2
        assert isinstance(data["models"], list)
        assert len(data["models"]) <= 20  # Limited to first 20
        
        mock_model_discovery_service.refresh_cache.assert_called_once()
    
    @patch('src.api.dependencies.get_model_discovery_service')
    def test_refresh_cache_service_error(self, mock_get_service, client):
        """Test error handling when refresh fails."""
        mock_service = Mock()
        mock_service.refresh_cache.side_effect = Exception("Refresh failed")
        mock_get_service.return_value = mock_service
        
        response = client.post("/api/models/refresh")
        
        assert response.status_code == 500
        assert "Failed to refresh model cache" in response.json()["detail"]


class TestProvidersEndpoint:
    """Test /api/models/providers endpoint."""
    
    @patch('src.api.dependencies.get_model_discovery_service')
    def test_get_providers_success(self, mock_get_service, client, mock_model_discovery_service):
        """Test successful provider information retrieval."""
        mock_get_service.return_value = mock_model_discovery_service
        
        response = client.get("/api/models/providers")
        
        assert response.status_code == 200
        data = response.json()
        
        assert "openai" in data
        assert "anthropic" in data
        assert "google" in data
        
        # Check provider structure
        openai_info = data["openai"]
        assert openai_info["name"] == "openai"
        assert openai_info["model_count"] == 3
        assert isinstance(openai_info["models"], list)
        assert "gpt-4o" in openai_info["models"]
    
    @patch('src.api.dependencies.get_model_discovery_service')
    def test_get_providers_service_error(self, mock_get_service, client):
        """Test error handling when provider service fails."""
        mock_service = Mock()
        mock_service.get_models_by_provider.side_effect = Exception("Provider fetch failed")
        mock_get_service.return_value = mock_service
        
        response = client.get("/api/models/providers")
        
        assert response.status_code == 500
        assert "Failed to get provider information" in response.json()["detail"]


class TestValidateModelEndpoint:
    """Test /api/models/validate/{model_name} endpoint."""
    
    @patch('src.api.dependencies.get_model_discovery_service')
    def test_validate_model_valid(self, mock_get_service, client):
        """Test validation of valid model."""
        mock_service = Mock()
        mock_service.find_best_match.return_value = ModelMatch(
            matched_name="gpt-4o",
            original_name="gpt-4o",
            confidence=1.0,
            match_type="exact"
        )
        mock_get_service.return_value = mock_service
        
        response = client.get("/api/models/validate/gpt-4o")
        
        assert response.status_code == 200
        data = response.json()
        
        assert data["valid"] is True
        assert data["model_name"] == "gpt-4o"
        assert data["matched_name"] == "gpt-4o"
        assert data["confidence"] == 1.0
        assert data["match_type"] == "exact"
    
    @patch('src.api.dependencies.get_model_discovery_service')
    def test_validate_model_low_confidence(self, mock_get_service, client):
        """Test validation with low confidence match."""
        mock_service = Mock()
        mock_service.find_best_match.return_value = ModelMatch(
            matched_name="gpt-4o",
            original_name="gpt4",
            confidence=0.7,
            match_type="fuzzy"
        )
        mock_service.search_models.return_value = [
            ("gpt-4o", 0.9),
            ("gpt-4o-mini", 0.8)
        ]
        mock_get_service.return_value = mock_service
        
        response = client.get("/api/models/validate/gpt4")
        
        assert response.status_code == 200
        data = response.json()
        
        assert data["valid"] is False
        assert data["model_name"] == "gpt4"
        assert "suggestions" in data
        assert len(data["suggestions"]) == 2
        assert data["suggestions"][0]["name"] == "gpt-4o"
        assert "not found" in data["message"]
    
    @patch('src.api.dependencies.get_model_discovery_service')
    def test_validate_model_no_match(self, mock_get_service, client):
        """Test validation with no match found."""
        mock_service = Mock()
        mock_service.find_best_match.return_value = None
        mock_service.search_models.return_value = []
        mock_get_service.return_value = mock_service
        
        response = client.get("/api/models/validate/unknown")
        
        assert response.status_code == 200
        data = response.json()
        
        assert data["valid"] is False
        assert data["model_name"] == "unknown"
        assert data["suggestions"] == []
    
    @patch('src.api.dependencies.get_model_discovery_service')
    def test_validate_model_service_error(self, mock_get_service, client):
        """Test error handling when validation service fails."""
        mock_service = Mock()
        mock_service.find_best_match.side_effect = Exception("Validation failed")
        mock_get_service.return_value = mock_service
        
        response = client.get("/api/models/validate/test")
        
        assert response.status_code == 500
        assert "Failed to validate model" in response.json()["detail"]


class TestModelRegistryIntegration:
    """Integration tests for model registry endpoints."""
    
    @patch('src.api.dependencies.get_model_discovery_service')
    def test_workflow_search_then_match(self, mock_get_service, client, mock_model_discovery_service):
        """Test realistic workflow: search then match."""
        mock_get_service.return_value = mock_model_discovery_service
        
        # First search for models
        search_response = client.get("/api/models/search?q=gpt")
        assert search_response.status_code == 200
        
        # Then match a specific model
        match_response = client.get("/api/models/match?name=gpt4o")
        assert match_response.status_code == 200
        
        # Verify both calls were made
        mock_model_discovery_service.search_models.assert_called_once()
        mock_model_discovery_service.find_best_match.assert_called_once()
    
    @patch('src.api.dependencies.get_model_discovery_service')
    def test_workflow_validate_then_refresh(self, mock_get_service, client):
        """Test workflow: validate model then refresh cache."""
        mock_service = Mock()
        mock_service.find_best_match.return_value = None
        mock_service.search_models.return_value = []
        mock_service.refresh_cache.return_value = {"new-model": Mock()}
        mock_get_service.return_value = mock_service
        
        # First validate (fails)
        validate_response = client.get("/api/models/validate/new-model")
        assert validate_response.status_code == 200
        assert validate_response.json()["valid"] is False
        
        # Then refresh cache
        refresh_response = client.post("/api/models/refresh")
        assert refresh_response.status_code == 200
        
        # Verify both calls
        mock_service.find_best_match.assert_called_once()
        mock_service.refresh_cache.assert_called_once()


class TestModelRegistryResponseFormats:
    """Test response format consistency."""
    
    @patch('src.api.dependencies.get_model_discovery_service')
    def test_all_endpoints_return_json(self, mock_get_service, client, mock_model_discovery_service):
        """Test that all endpoints return valid JSON."""
        mock_get_service.return_value = mock_model_discovery_service
        
        endpoints = [
            ("/api/models/supported", "GET"),
            ("/api/models/search?q=test", "GET"),
            ("/api/models/match?name=test", "GET"),
            ("/api/models/providers", "GET"),
            ("/api/models/validate/test", "GET"),
            ("/api/models/refresh", "POST")
        ]
        
        for endpoint, method in endpoints:
            if method == "GET":
                response = client.get(endpoint)
            else:
                response = client.post(endpoint)
            
            assert response.status_code in [200, 404, 422, 500]
            assert response.headers["content-type"] == "application/json"
            
            # Should be valid JSON
            data = response.json()
            assert isinstance(data, (dict, list))