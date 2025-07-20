import pytest
from unittest.mock import patch, MagicMock
import sys
from pathlib import Path

# Add the parent directory to the path so we can import main
sys.path.insert(0, str(Path(__file__).parent.parent))

from main import normalize_model, calculate_impact, CONFIG


class TestModelNormalization:
    """Test model name normalization functionality"""

    def test_normalize_model_mapped(self):
        """Test normalization with mapped model names"""
        test_cases = [
            ("gpt-4o", "gpt-4o-2024-05-13"),
            ("GPT-4O", "gpt-4o-2024-05-13"),  # Case insensitive
            ("claude-3-opus", "claude-3-opus-20240229"),
            ("gemini-pro", "gemini-1.0-pro")
        ]
        
        for input_model, expected_output in test_cases:
            result = normalize_model(input_model)
            assert result == expected_output

    def test_normalize_model_unmapped(self):
        """Test normalization with unmapped model names"""
        unmapped_models = [
            "unknown-model",
            "custom-model-v1",
            "test-model-123"
        ]
        
        for model in unmapped_models:
            result = normalize_model(model)
            assert result == model  # Should return original name

    def test_normalize_model_case_insensitive_mapping(self):
        """Test that model mapping is case insensitive"""
        variations = [
            "gpt-4o",
            "GPT-4O", 
            "Gpt-4o",
            "gPt-4O"
        ]
        
        expected = "gpt-4o-2024-05-13"
        
        for variation in variations:
            result = normalize_model(variation)
            assert result == expected

    def test_normalize_model_empty_string(self):
        """Test normalization with empty string"""
        result = normalize_model("")
        assert result == ""

    def test_normalize_model_none_in_mappings(self):
        """Test behavior when model mapping returns None"""
        with patch.dict(CONFIG["model_mappings"], {"test-model": None}):
            result = normalize_model("test-model")
            assert result is None


class TestImpactCalculation:
    """Test environmental impact calculation functionality"""

    def test_calculate_impact_negative_input_tokens(self):
        """Test calculation with negative input tokens"""
        result = calculate_impact("gpt-4o", -100, 500)
        
        assert result['energy_kwh'] == 0
        assert result['gwp_kgco2eq'] == 0
        assert result['success'] is False
        assert "Token counts must be non-negative" in result['error']

    def test_calculate_impact_negative_output_tokens(self):
        """Test calculation with negative output tokens"""
        result = calculate_impact("gpt-4o", 1000, -50)
        
        assert result['energy_kwh'] == 0
        assert result['gwp_kgco2eq'] == 0
        assert result['success'] is False
        assert "Token counts must be non-negative" in result['error']

    def test_calculate_impact_both_negative_tokens(self):
        """Test calculation with both negative token counts"""
        result = calculate_impact("gpt-4o", -100, -50)
        
        assert result['energy_kwh'] == 0
        assert result['gwp_kgco2eq'] == 0
        assert result['success'] is False
        assert "Token counts must be non-negative" in result['error']

    def test_calculate_impact_zero_tokens(self):
        """Test calculation with zero tokens"""
        with patch('main.models', {'gpt-4o-2024-05-13': MagicMock()}):
            with patch('main.Impacts') as mock_impacts_class:
                mock_impacts = MagicMock()
                mock_impacts.energy.value = 0.0
                mock_impacts.gwp.value = 0.0
                mock_impacts_class.from_model_and_tokens.return_value = mock_impacts
                
                result = calculate_impact("gpt-4o", 0, 0)
                
                assert result['energy_kwh'] == 0.0
                assert result['gwp_kgco2eq'] == 0.0
                assert result['success'] is True

    def test_calculate_impact_supported_model(self, mock_models, mock_ecologits):
        """Test calculation with supported model"""
        result = calculate_impact("gpt-4o", 1000, 500)
        
        assert result['energy_kwh'] == 0.001234
        assert result['gwp_kgco2eq'] == 0.000567
        assert result['success'] is True
        assert result['normalized_model'] == 'gpt-4o-2024-05-13'
        assert 'error' not in result

    def test_calculate_impact_unsupported_model(self):
        """Test calculation with unsupported model"""
        with patch('main.models', {}):  # Empty models dict
            result = calculate_impact("unknown-model", 1000, 500)
            
            assert result['energy_kwh'] == 0
            assert result['gwp_kgco2eq'] == 0
            assert result['success'] is False
            assert "Model 'unknown-model' not supported" in result['error']

    def test_calculate_impact_ecologits_exception(self, mock_models):
        """Test calculation when ecologits raises an exception"""
        with patch('main.Impacts') as mock_impacts_class:
            mock_impacts_class.from_model_and_tokens.side_effect = Exception("Calculation failed")
            
            result = calculate_impact("gpt-4o", 1000, 500)
            
            assert result['energy_kwh'] == 0
            assert result['gwp_kgco2eq'] == 0
            assert result['success'] is False
            assert result['error'] == 'Internal calculation error'

    def test_calculate_impact_normalize_model_called(self, mock_models, mock_ecologits):
        """Test that model normalization is called during calculation"""
        with patch('main.normalize_model') as mock_normalize:
            mock_normalize.return_value = "gpt-4o-2024-05-13"
            
            calculate_impact("GPT-4O", 1000, 500)
            
            mock_normalize.assert_called_once_with("GPT-4O")

    def test_calculate_impact_large_token_counts(self, mock_models, mock_ecologits):
        """Test calculation with large token counts"""
        result = calculate_impact("gpt-4o", 1000000, 500000)
        
        assert result['success'] is True
        assert result['energy_kwh'] == 0.001234
        assert result['gwp_kgco2eq'] == 0.000567

    def test_calculate_impact_model_mapping_integration(self, mock_models, mock_ecologits):
        """Test that model mapping works correctly in calculation"""
        # Test with a model that needs mapping
        result = calculate_impact("claude-3-opus", 1000, 500)
        
        assert result['success'] is True
        assert result['normalized_model'] == 'claude-3-opus-20240229'

    def test_calculate_impact_returns_float_values(self, mock_models, mock_ecologits):
        """Test that calculation returns proper float values"""
        result = calculate_impact("gpt-4o", 1000, 500)
        
        assert isinstance(result['energy_kwh'], float)
        assert isinstance(result['gwp_kgco2eq'], float)
        assert result['energy_kwh'] > 0
        assert result['gwp_kgco2eq'] > 0

    def test_calculate_impact_ecologits_model_parameters(self, mock_models, mock_ecologits):
        """Test that correct parameters are passed to ecologits"""
        calculate_impact("gpt-4o", 1000, 500)
        
        # Verify that Impacts.from_model_and_tokens was called with correct parameters
        mock_ecologits.from_model_and_tokens.assert_called_once()
        call_args = mock_ecologits.from_model_and_tokens.call_args
        
        assert call_args[1]['input_tokens'] == 1000
        assert call_args[1]['output_tokens'] == 500
        # Model should be the normalized version
        assert call_args[1]['model'] is not None