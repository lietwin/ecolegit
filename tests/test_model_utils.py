"""Tests for model utilities."""
import pytest
from src.domain.model_utils import detect_provider


class TestDetectProvider:
    """Test provider detection functionality."""

    def test_detect_openai_gpt_prefix(self):
        """Test detection of OpenAI models with gpt- prefix."""
        assert detect_provider("gpt-4") == "openai"
        assert detect_provider("gpt-3.5-turbo") == "openai"
        assert detect_provider("gpt-4o") == "openai"

    def test_detect_openai_gpt_contains(self):
        """Test detection of OpenAI models containing 'gpt'."""
        assert detect_provider("chatgpt") == "openai"
        assert detect_provider("some-gpt-model") == "openai"

    def test_detect_anthropic_claude_prefix(self):
        """Test detection of Anthropic models with claude- prefix."""
        assert detect_provider("claude-3") == "anthropic"
        assert detect_provider("claude-3-opus") == "anthropic"
        assert detect_provider("claude-3.5-sonnet") == "anthropic"

    def test_detect_anthropic_claude_contains(self):
        """Test detection of Anthropic models containing 'claude'."""
        assert detect_provider("claude") == "anthropic"
        assert detect_provider("some-claude-model") == "anthropic"

    def test_detect_google_gemini_prefix(self):
        """Test detection of Google models with gemini- prefix."""
        assert detect_provider("gemini-pro") == "google_genai"
        assert detect_provider("gemini-1.5-pro") == "google_genai"

    def test_detect_google_gemini_contains(self):
        """Test detection of Google models containing 'gemini'."""
        assert detect_provider("gemini") == "google_genai"
        assert detect_provider("some-gemini-model") == "google_genai"

    def test_detect_cohere_command_prefix(self):
        """Test detection of Cohere command models."""
        assert detect_provider("command") == "cohere"
        assert detect_provider("command-r") == "cohere"
        assert detect_provider("command-r-plus") == "cohere"

    def test_detect_cohere_embed_prefix(self):
        """Test detection of Cohere embed models."""
        assert detect_provider("embed") == "cohere"
        assert detect_provider("embed-english-v3.0") == "cohere"

    def test_detect_mistral_prefix(self):
        """Test detection of Mistral models."""
        assert detect_provider("mistral") == "mistralai"
        assert detect_provider("mistral-7b") == "mistralai"
        assert detect_provider("mixtral") == "mistralai"
        assert detect_provider("mixtral-8x7b") == "mistralai"

    def test_case_insensitive_detection(self):
        """Test that provider detection is case insensitive."""
        assert detect_provider("GPT-4") == "openai"
        assert detect_provider("CLAUDE-3") == "anthropic"
        assert detect_provider("GEMINI-PRO") == "google_genai"
        assert detect_provider("COMMAND") == "cohere"
        assert detect_provider("MISTRAL") == "mistralai"

    def test_unknown_models_handled_gracefully(self):
        """Test that unknown models are handled gracefully with fallback."""
        result = detect_provider("unknown-model")
        assert isinstance(result, str)
        assert result == "openai"  # Current fallback behavior
        
        result = detect_provider("some-random-model")
        assert isinstance(result, str)
        assert result == "openai"
        
        result = detect_provider("")
        assert isinstance(result, str)
        assert result == "openai"
        
        result = detect_provider("llama-2")
        assert isinstance(result, str)
        assert result == "openai"

    def test_edge_cases(self):
        """Test edge cases for provider detection."""
        assert detect_provider("gpt") == "openai"
        assert detect_provider("claude") == "anthropic"
        assert detect_provider("gemini") == "google_genai"
        assert detect_provider("command") == "cohere"
        assert detect_provider("embed") == "cohere"
        assert detect_provider("mistral") == "mistralai"
        assert detect_provider("mixtral") == "mistralai"