"""Unit tests for model normalization functions."""

import pytest
import sys
from pathlib import Path

# Add the parent directory to the path
sys.path.insert(0, str(Path(__file__).parent.parent))

from src.domain.model_normalizer import (
    normalize_model_name,
    find_similar_models,
    get_suggestion_message
)


class TestNormalizeModelName:
    """Test the normalize_model_name function."""
    
    def test_gpt_variations(self):
        """Test GPT model variations are normalized correctly."""
        test_cases = [
            ("gpt4o", "gpt-4o"),
            ("gpt-4o", "gpt-4o"),  # Already correct
            ("GPT4O", "gpt-4o"),   # Case insensitive
            ("gpt4omini", "gpt-4o-mini"),
            ("gpt-4omini", "gpt-4o-mini"),
            ("gpt4o-mini", "gpt-4o-mini"),
            ("gpt35turbo", "gpt-3.5-turbo"),
            ("gpt-35-turbo", "gpt-3.5-turbo"),
            ("gpt3.5turbo", "gpt-3.5-turbo"),
            ("gpt4", "gpt-4"),
        ]
        
        for input_name, expected in test_cases:
            result = normalize_model_name(input_name)
            assert result == expected, f"Expected '{input_name}' -> '{expected}', got '{result}'"
    
    def test_claude_variations(self):
        """Test Claude model variations are normalized correctly."""
        test_cases = [
            ("claudeopus", "claude-3-opus"),
            ("claude3opus", "claude-3-opus"),
            ("claude-3opus", "claude-3-opus"),
            ("claudesonnet", "claude-3-sonnet"),
            ("claude3sonnet", "claude-3-sonnet"),
            ("claude-3sonnet", "claude-3-sonnet"),
            ("claudehaiku", "claude-3-haiku"),
            ("claude3haiku", "claude-3-haiku"),
            ("claude35sonnet", "claude-3-5-sonnet"),
            ("claude-35-sonnet", "claude-3-5-sonnet"),
            ("claude3.5sonnet", "claude-3-5-sonnet"),
        ]
        
        for input_name, expected in test_cases:
            result = normalize_model_name(input_name)
            assert result == expected, f"Expected '{input_name}' -> '{expected}', got '{result}'"
    
    def test_gemini_variations(self):
        """Test Gemini model variations are normalized correctly."""
        test_cases = [
            ("geminipro", "gemini-pro"),
            ("gemini1.5pro", "gemini-1.5-pro"),
            ("gemini15pro", "gemini-1.5-pro"),
            ("gemini-15-pro", "gemini-1.5-pro"),
        ]
        
        for input_name, expected in test_cases:
            result = normalize_model_name(input_name)
            assert result == expected, f"Expected '{input_name}' -> '{expected}', got '{result}'"
    
    def test_case_insensitive(self):
        """Test that normalization is case insensitive."""
        test_cases = [
            ("GPT4O", "gpt-4o"),
            ("ClaudeOpus", "claude-3-opus"),
            ("GEMINIPRO", "gemini-pro"),
            ("gPt4O", "gpt-4o"),
        ]
        
        for input_name, expected in test_cases:
            result = normalize_model_name(input_name)
            assert result == expected, f"Expected '{input_name}' -> '{expected}', got '{result}'"
    
    def test_whitespace_handling(self):
        """Test that whitespace is stripped properly."""
        test_cases = [
            ("  gpt4o  ", "gpt-4o"),
            (" claudeopus ", "claude-3-opus"),
            ("gpt4o\n", "gpt-4o"),
            ("\tgeminipro\t", "gemini-pro"),
        ]
        
        for input_name, expected in test_cases:
            result = normalize_model_name(input_name)
            assert result == expected, f"Expected '{input_name}' -> '{expected}', got '{result}'"
    
    def test_unknown_models_unchanged(self):
        """Test that unknown model names are returned unchanged."""
        test_cases = [
            "unknown-model",
            "random-name",
            "not-a-model",
            "xyz-123"
        ]
        
        for model_name in test_cases:
            result = normalize_model_name(model_name)
            assert result == model_name, f"Unknown model '{model_name}' should be unchanged"
    
    def test_empty_and_none_input(self):
        """Test edge cases with empty or None input."""
        assert normalize_model_name("") == ""
        assert normalize_model_name("   ") == "   "  # Preserve whitespace-only input
        assert normalize_model_name(None) == None
    
    def test_already_correct_models_unchanged(self):
        """Test that correctly formatted model names are unchanged."""
        correct_names = [
            "gpt-4o",
            "gpt-4o-mini", 
            "claude-3-opus",
            "claude-3-sonnet",
            "claude-3-haiku",
            "claude-3-5-sonnet",
            "gemini-pro",
            "gemini-1.5-pro"
        ]
        
        for model_name in correct_names:
            result = normalize_model_name(model_name)
            assert result == model_name, f"Correct model '{model_name}' should be unchanged"


class TestFindSimilarModels:
    """Test the find_similar_models function."""
    
    def setup_method(self):
        """Set up test data."""
        self.available_models = [
            "gpt-4o",
            "gpt-4o-mini",
            "claude-3-opus", 
            "claude-3-sonnet",
            "claude-3-haiku",
            "gemini-pro",
            "gemini-1.5-pro"
        ]
    
    def test_finds_similar_models(self):
        """Test that similar models are found correctly."""
        result = find_similar_models("gpt4o", self.available_models)
        
        assert len(result) > 0
        assert any("gpt-4o" in match[0] for match in result)
        
        # Results should be sorted by similarity score (descending)
        if len(result) > 1:
            assert result[0][1] >= result[1][1]
    
    def test_substring_matching(self):
        """Test that substring matching works."""
        result = find_similar_models("claude", self.available_models)
        
        claude_matches = [match for match in result if "claude" in match[0]]
        assert len(claude_matches) > 0
    
    def test_no_matches_for_very_different_name(self):
        """Test that very different names return few or no matches."""
        result = find_similar_models("completely-different-model", self.available_models)
        
        # Should return empty list or very low scores
        assert len(result) == 0 or all(score < 0.6 for _, score in result)
    
    def test_empty_input_handling(self):
        """Test edge cases with empty inputs."""
        assert find_similar_models("", self.available_models) == []
        assert find_similar_models("test", []) == []
        assert find_similar_models("", []) == []
    
    def test_exact_match_gets_highest_score(self):
        """Test that exact matches get highest similarity score."""
        result = find_similar_models("gpt-4o", self.available_models)
        
        assert len(result) > 0
        assert result[0][0] == "gpt-4o"
        assert result[0][1] == 1.0  # Perfect match
    
    def test_returns_max_three_suggestions(self):
        """Test that function returns at most 3 suggestions."""
        result = find_similar_models("gpt", self.available_models)
        
        assert len(result) <= 3


class TestGetSuggestionMessage:
    """Test the get_suggestion_message function."""
    
    def setup_method(self):
        """Set up test data."""
        self.available_models = [
            "gpt-4o",
            "gpt-4o-mini",
            "claude-3-opus",
            "claude-3-sonnet"
        ]
    
    def test_single_suggestion_message(self):
        """Test message format for single suggestion."""
        # Mock find_similar_models to return single result
        import src.domain.model_normalizer as normalizer
        original_find = normalizer.find_similar_models
        
        def mock_find(name, models):
            return [("gpt-4o", 0.8)]
        
        normalizer.find_similar_models = mock_find
        
        try:
            message = get_suggestion_message("gpt4o", self.available_models)
            assert "Did you mean 'gpt-4o'?" in message
            assert "gpt4o" in message
        finally:
            normalizer.find_similar_models = original_find
    
    def test_multiple_suggestions_message(self):
        """Test message format for multiple suggestions."""
        import src.domain.model_normalizer as normalizer
        original_find = normalizer.find_similar_models
        
        def mock_find(name, models):
            return [("gpt-4o", 0.8), ("gpt-4o-mini", 0.7)]
        
        normalizer.find_similar_models = mock_find
        
        try:
            message = get_suggestion_message("gpt4o", self.available_models)
            assert "Did you mean:" in message
            assert "gpt-4o" in message
            assert "gpt-4o-mini" in message
        finally:
            normalizer.find_similar_models = original_find
    
    def test_no_suggestions_message(self):
        """Test message when no suggestions are found."""
        import src.domain.model_normalizer as normalizer
        original_find = normalizer.find_similar_models
        
        def mock_find(name, models):
            return []
        
        normalizer.find_similar_models = mock_find
        
        try:
            message = get_suggestion_message("unknown", self.available_models)
            assert "not supported" in message
            assert "Check /models" in message
        finally:
            normalizer.find_similar_models = original_find
    
    def test_empty_input_handling(self):
        """Test edge cases with empty inputs."""
        message = get_suggestion_message("", self.available_models)
        assert "not supported" in message or "not found" in message
        
        message = get_suggestion_message("test", [])
        assert "not supported" in message or "not found" in message