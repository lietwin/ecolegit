"""Tests for security validation of model names."""
import pytest
from unittest.mock import Mock, patch

from src.domain.services import ImpactCalculationService
from src.config.settings import AppConfig


class TestSecurityValidation:
    """Test security validation for both original and normalized model names."""

    @pytest.fixture
    def mock_ecologits_repo(self):
        """Create mock ecologits repository."""
        repo = Mock()
        repo.is_model_supported.return_value = True
        return repo

    @pytest.fixture
    def mock_config(self):
        """Create mock config."""
        config = Mock(spec=AppConfig)
        config.model_mappings = {}
        return config

    @pytest.fixture
    def service(self, mock_ecologits_repo, mock_config):
        """Create impact calculation service."""
        return ImpactCalculationService(mock_ecologits_repo, mock_config)

    def test_validate_model_name_security_valid_names(self, service):
        """Test that valid model names pass security validation."""
        valid_names = [
            "gpt-4",
            "claude-3-opus",
            "gemini-pro",
            "gpt-3.5-turbo",
            "model_with_underscores",
            "Model123",
            "test-model.v2"
        ]
        
        for name in valid_names:
            # Should not raise any exception
            service._validate_model_name_security(name)

    def test_validate_model_name_security_invalid_chars(self, service):
        """Test that model names with invalid characters are rejected."""
        invalid_names = [
            "model@invalid",
            "model with spaces",
            "model!special",
            "model#hash",
            "model$dollar",
            "model%percent",
            "model^caret",
            "model&ampersand",
            "model*asterisk",
            "model(parenthesis)",
            "model+plus",
            "model=equals",
            "model[brackets]",
            "model{braces}",
            "model|pipe",
            "model\\backslash",
            "model:colon",
            "model;semicolon",
            "model\"quote",
            "model'apostrophe",
            "model<less>",
            "model,comma",
            "model?question",
            "model/slash"
        ]
        
        for name in invalid_names:
            with pytest.raises(ValueError, match="Model name contains invalid characters"):
                service._validate_model_name_security(name)

    def test_validate_model_name_security_too_long(self, service):
        """Test that model names longer than 100 characters are rejected."""
        long_name = "a" * 101
        
        with pytest.raises(ValueError, match="Model name too long"):
            service._validate_model_name_security(long_name)

    def test_validate_model_name_security_empty_after_strip(self, service):
        """Test that model names that are empty after stripping are rejected."""
        empty_names = [
            "",
            "   ",
            "\t",
            "\n",
            "   \t \n  "
        ]
        
        for name in empty_names:
            with pytest.raises(ValueError, match="Model name cannot be empty after normalization"):
                service._validate_model_name_security(name)

    def test_normalize_model_validates_normalized_result(self, service, mock_ecologits_repo):
        """Test that normalization validates the normalized result."""
        # Mock a normalization that would produce an invalid result
        with patch('src.domain.model_normalizer.normalize_model_name', return_value="invalid@model"):
            with pytest.raises(ValueError, match="Model name contains invalid characters"):
                service._normalize_model("gpt4")

    def test_normalize_model_validates_mapped_result(self, service, mock_config):
        """Test that mapped model names are also validated."""
        # Set up config mapping that maps to an invalid model name
        mock_config.model_mappings = {"gpt4": "invalid@mapped"}
        
        with patch('src.domain.model_normalizer.normalize_model_name', return_value="gpt4"):
            with pytest.raises(ValueError, match="Model name contains invalid characters"):
                service._normalize_model("gpt4")

    def test_security_validation_prevents_normalization_bypass(self, service, mock_config):
        """Test that security validation prevents bypassing original validation via normalization."""
        # Scenario: Input passes Pydantic validation but normalization produces invalid result
        
        # Mock normalization to return something that would fail security validation
        with patch('src.domain.model_normalizer.normalize_model_name', return_value="bypassed@security"):
            with pytest.raises(ValueError, match="Model name contains invalid characters"):
                service._normalize_model("gpt-4")  # Valid input, invalid normalized output

    def test_edge_case_special_chars_in_allowed_set(self, service):
        """Test edge cases with the allowed special characters."""
        # Test combinations of allowed characters
        valid_combinations = [
            "a-b",
            "a.b", 
            "a_b",
            "a-b.c_d",
            "test-model.v1_final",
            "123-456.789_abc"
        ]
        
        for name in valid_combinations:
            # Should not raise
            service._validate_model_name_security(name)

    def test_unicode_characters_rejected(self, service):
        """Test that unicode/non-ASCII characters are rejected."""
        unicode_names = [
            "model-名前",
            "model-тест", 
            "model-🚀",
            "model-café",
            "model-naïve"
        ]
        
        for name in unicode_names:
            with pytest.raises(ValueError, match="Model name contains invalid characters"):
                service._validate_model_name_security(name)