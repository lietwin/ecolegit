"""Tests for model discovery service."""

import pytest
import time
from unittest.mock import Mock, MagicMock
from src.domain.model_discovery import ModelDiscoveryService, ModelInfo, ModelMatch


class MockEcologitsRepo:
    """Mock EcoLogits repository for testing."""
    
    def __init__(self, models_dict=None):
        self.models_dict = models_dict or {
            "gpt-4o": Mock(name="gpt-4o"),
            "gpt-4o-mini": Mock(name="gpt-4o-mini"),
            "gpt-3.5-turbo": Mock(name="gpt-3.5-turbo"),
            "claude-3-opus": Mock(name="claude-3-opus"),
            "claude-3-sonnet": Mock(name="claude-3-sonnet"),
            "gemini-1.5-pro": Mock(name="gemini-1.5-pro")
        }
    
    def get_available_models(self):
        return self.models_dict


@pytest.fixture
def mock_ecologits_repo():
    """Create mock EcoLogits repository."""
    return MockEcologitsRepo()


@pytest.fixture
def model_discovery_service(mock_ecologits_repo):
    """Create ModelDiscoveryService with mock repo."""
    return ModelDiscoveryService(mock_ecologits_repo, cache_ttl_seconds=1)


@pytest.fixture
def populated_service(mock_ecologits_repo):
    """Create service with pre-populated cache."""
    service = ModelDiscoveryService(mock_ecologits_repo, cache_ttl_seconds=3600)
    service.discover_models()  # Populate cache
    return service


class TestModelDiscoveryService:
    """Test ModelDiscoveryService functionality."""
    
    def test_discover_models_initial_load(self, model_discovery_service):
        """Test initial model discovery."""
        models = model_discovery_service.discover_models()
        
        assert len(models) == 6
        assert "gpt-4o" in models
        assert "claude-3-opus" in models
        assert models["gpt-4o"].provider == "openai"
        assert models["claude-3-opus"].provider == "anthropic"
        assert models["gemini-1.5-pro"].provider == "google"
    
    def test_discover_models_caching(self, model_discovery_service):
        """Test that models are cached and not re-fetched."""
        # First call
        models1 = model_discovery_service.discover_models()
        timestamp1 = model_discovery_service._cache_timestamp
        
        # Second call should use cache
        models2 = model_discovery_service.discover_models()
        timestamp2 = model_discovery_service._cache_timestamp
        
        assert models1 == models2
        assert timestamp1 == timestamp2
    
    def test_discover_models_cache_expiry(self, model_discovery_service):
        """Test cache expiration and refresh."""
        # First call
        models1 = model_discovery_service.discover_models()
        timestamp1 = model_discovery_service._cache_timestamp
        
        # Wait for cache to expire
        time.sleep(1.1)
        
        # Second call should refresh cache
        models2 = model_discovery_service.discover_models()
        timestamp2 = model_discovery_service._cache_timestamp
        
        assert timestamp2 > timestamp1
    
    def test_discover_models_force_refresh(self, model_discovery_service):
        """Test force refresh of cache."""
        # Initial load
        model_discovery_service.discover_models()
        timestamp1 = model_discovery_service._cache_timestamp
        
        # Force refresh
        models = model_discovery_service.discover_models(force_refresh=True)
        timestamp2 = model_discovery_service._cache_timestamp
        
        assert timestamp2 > timestamp1
        assert len(models) == 6
    
    def test_discover_models_handles_exceptions(self):
        """Test error handling in model discovery."""
        failing_repo = Mock()
        failing_repo.get_available_models.side_effect = Exception("Connection failed")
        
        service = ModelDiscoveryService(failing_repo)
        models = service.discover_models()
        
        assert models == {}
    
    def test_find_best_match_exact(self, populated_service):
        """Test exact model name matching."""
        match = populated_service.find_best_match("gpt-4o")
        
        assert match is not None
        assert match.matched_name == "gpt-4o"
        assert match.original_name == "gpt-4o"
        assert match.confidence == 1.0
        assert match.match_type == "exact"
    
    def test_find_best_match_case_insensitive(self, populated_service):
        """Test case-insensitive exact matching."""
        match = populated_service.find_best_match("GPT-4O")
        
        assert match is not None
        assert match.matched_name == "gpt-4o"
        assert match.confidence == 1.0
        assert match.match_type == "exact"
    
    def test_find_best_match_alias(self, populated_service):
        """Test alias matching."""
        match = populated_service.find_best_match("gpt4o")  # No hyphens
        
        assert match is not None
        assert match.matched_name == "gpt-4o"
        assert match.confidence == 0.95
        assert match.match_type == "alias"
    
    def test_find_best_match_transform(self, populated_service):
        """Test common transform matching."""
        match = populated_service.find_best_match("claude3-opus")
        
        assert match is not None
        assert match.matched_name == "claude-3-opus"
        assert match.confidence == 0.9
        assert match.match_type == "transform"
    
    def test_find_best_match_fuzzy(self, populated_service):
        """Test fuzzy matching."""
        match = populated_service.find_best_match("gpt4-o")  # Slight variation
        
        assert match is not None
        assert match.matched_name == "gpt-4o"
        assert match.confidence >= 0.6
        assert match.match_type == "fuzzy"
    
    def test_find_best_match_no_match(self, populated_service):
        """Test no match found."""
        match = populated_service.find_best_match("completely-unknown-model")
        
        assert match is None
    
    def test_find_best_match_empty_cache(self, model_discovery_service):
        """Test matching with empty cache."""
        # Don't populate cache
        match = model_discovery_service.find_best_match("gpt-4o")
        
        # Should still work by discovering models
        assert match is not None
        assert match.matched_name == "gpt-4o"
    
    def test_get_supported_models(self, populated_service):
        """Test getting supported models list."""
        models = populated_service.get_supported_models()
        
        assert isinstance(models, list)
        assert len(models) == 6
        assert "gpt-4o" in models
        assert "claude-3-opus" in models
        assert models == sorted(models)  # Should be sorted
    
    def test_get_models_by_provider(self, populated_service):
        """Test getting models grouped by provider."""
        by_provider = populated_service.get_models_by_provider()
        
        assert "openai" in by_provider
        assert "anthropic" in by_provider
        assert "google" in by_provider
        
        assert "gpt-4o" in by_provider["openai"]
        assert "claude-3-opus" in by_provider["anthropic"]
        assert "gemini-1.5-pro" in by_provider["google"]
        
        # Check sorting
        for provider_models in by_provider.values():
            assert provider_models == sorted(provider_models)
    
    def test_search_models_empty_query(self, populated_service):
        """Test search with empty query."""
        results = populated_service.search_models("", limit=3)
        
        assert len(results) == 3
        assert all(isinstance(item, tuple) for item in results)
        assert all(len(item) == 2 for item in results)
    
    def test_search_models_substring_match(self, populated_service):
        """Test search with substring match."""
        results = populated_service.search_models("gpt", limit=5)
        
        # Should find all GPT models
        model_names = [name for name, score in results]
        assert any("gpt-4o" in name for name in model_names)
        assert any("gpt-3.5-turbo" in name for name in model_names)
        
        # Scores should be reasonable
        assert all(0.3 <= score <= 1.0 for name, score in results)
    
    def test_search_models_fuzzy_match(self, populated_service):
        """Test search with fuzzy matching."""
        results = populated_service.search_models("claude", limit=5)
        
        # Should find Claude models
        model_names = [name for name, score in results]
        assert any("claude" in name.lower() for name in model_names)
    
    def test_search_models_limit(self, populated_service):
        """Test search result limiting."""
        results = populated_service.search_models("", limit=2)
        
        assert len(results) <= 2
    
    def test_refresh_cache(self, populated_service):
        """Test cache refresh method."""
        original_timestamp = populated_service._cache_timestamp
        
        models = populated_service.refresh_cache()
        
        assert populated_service._cache_timestamp > original_timestamp
        assert len(models) == 6
    
    def test_extract_provider_openai(self, model_discovery_service):
        """Test provider extraction for OpenAI models."""
        assert model_discovery_service._extract_provider("gpt-4o") == "openai"
        assert model_discovery_service._extract_provider("gpt-3.5-turbo") == "openai"
        assert model_discovery_service._extract_provider("davinci") == "openai"
    
    def test_extract_provider_anthropic(self, model_discovery_service):
        """Test provider extraction for Anthropic models."""
        assert model_discovery_service._extract_provider("claude-3-opus") == "anthropic"
        assert model_discovery_service._extract_provider("claude-2") == "anthropic"
    
    def test_extract_provider_google(self, model_discovery_service):
        """Test provider extraction for Google models."""
        assert model_discovery_service._extract_provider("gemini-1.5-pro") == "google"
        assert model_discovery_service._extract_provider("palm-2") == "google"
    
    def test_extract_provider_unknown(self, model_discovery_service):
        """Test provider extraction for unknown models."""
        assert model_discovery_service._extract_provider("unknown-model") == "unknown"
    
    def test_generate_aliases_no_hyphens(self, model_discovery_service):
        """Test alias generation for hyphenated names."""
        aliases = model_discovery_service._generate_aliases("gpt-4o")
        
        assert "gpt4o" in aliases
    
    def test_generate_aliases_version_stripping(self, model_discovery_service):
        """Test alias generation strips version numbers."""
        aliases = model_discovery_service._generate_aliases("gpt-4o-2024-05-13")
        
        assert "gpt4o20240513" in aliases  # No hyphens
        # Should also strip date
        assert any("gpt-4o" in alias for alias in aliases)
    
    def test_generate_aliases_turbo_variants(self, model_discovery_service):
        """Test alias generation for turbo models."""
        aliases = model_discovery_service._generate_aliases("gpt-3.5-turbo")
        
        assert "gpt35turbo" in aliases  # No hyphens
        assert "gpt-3.5-" in aliases  # Turbo removed


class TestModelInfo:
    """Test ModelInfo dataclass."""
    
    def test_model_info_creation(self):
        """Test ModelInfo creation."""
        model_info = ModelInfo(
            name="gpt-4o",
            provider="openai",
            available=True,
            aliases=["gpt4o"]
        )
        
        assert model_info.name == "gpt-4o"
        assert model_info.provider == "openai"
        assert model_info.available is True
        assert model_info.aliases == ["gpt4o"]


class TestModelMatch:
    """Test ModelMatch dataclass."""
    
    def test_model_match_creation(self):
        """Test ModelMatch creation."""
        match = ModelMatch(
            matched_name="gpt-4o",
            original_name="gpt4o",
            confidence=0.95,
            match_type="alias"
        )
        
        assert match.matched_name == "gpt-4o"
        assert match.original_name == "gpt4o"
        assert match.confidence == 0.95
        assert match.match_type == "alias"


class TestCommonTransforms:
    """Test common model name transformations."""
    
    def test_common_transforms_coverage(self, model_discovery_service):
        """Test that common transforms are properly defined."""
        transforms = model_discovery_service._common_transforms
        
        # Check key transformations
        assert transforms["gpt4o"] == "gpt-4o"
        assert transforms["gpt4o-mini"] == "gpt-4o-mini"
        assert transforms["claude3-opus"] == "claude-3-opus"
        assert transforms["claude35-sonnet"] == "claude-3-5-sonnet"