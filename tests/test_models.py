import pytest
from pydantic import ValidationError
import sys
from pathlib import Path

# Add the parent directory to the path so we can import main
sys.path.insert(0, str(Path(__file__).parent.parent))

from main import UsageRequest, ImpactResponse


class TestUsageRequest:
    """Test UsageRequest model validation"""

    def test_usage_request_valid(self):
        """Test valid usage request creation"""
        request = UsageRequest(
            model="gpt-4o",
            input_tokens=1000,
            output_tokens=500,
            metadata={"user": "test123"}
        )
        
        assert request.model == "gpt-4o"
        assert request.input_tokens == 1000
        assert request.output_tokens == 500
        assert request.metadata == {"user": "test123"}

    def test_usage_request_minimal(self):
        """Test minimal valid request without optional fields"""
        request = UsageRequest(
            model="gpt-4o",
            input_tokens=100,
            output_tokens=50
        )
        
        assert request.model == "gpt-4o"
        assert request.input_tokens == 100
        assert request.output_tokens == 50
        assert request.metadata is None

    def test_usage_request_model_validation_invalid_chars(self):
        """Test model name validation with invalid characters"""
        with pytest.raises(ValidationError) as exc_info:
            UsageRequest(
                model="gpt-4o@invalid!",
                input_tokens=100,
                output_tokens=50
            )
        
        assert "Model name contains invalid characters" in str(exc_info.value)

    def test_usage_request_model_validation_valid_chars(self):
        """Test model name validation with valid characters"""
        valid_models = [
            "gpt-4o",
            "claude_3_opus",
            "gemini.1.5.pro",
            "model123",
            "GPT-4O"  # Should be lowercased
        ]
        
        for model_name in valid_models:
            request = UsageRequest(
                model=model_name,
                input_tokens=100,
                output_tokens=50
            )
            assert request.model == model_name.strip().lower()

    def test_usage_request_empty_model_name(self):
        """Test validation with empty model name"""
        with pytest.raises(ValidationError) as exc_info:
            UsageRequest(
                model="",
                input_tokens=100,
                output_tokens=50
            )
        
        assert "at least 1 character" in str(exc_info.value)

    def test_usage_request_model_name_too_long(self):
        """Test validation with model name exceeding max length"""
        long_model_name = "a" * 101  # Exceeds 100 character limit
        
        with pytest.raises(ValidationError) as exc_info:
            UsageRequest(
                model=long_model_name,
                input_tokens=100,
                output_tokens=50
            )
        
        assert "at most 100 characters" in str(exc_info.value)

    def test_usage_request_negative_input_tokens(self):
        """Test validation with negative input tokens"""
        with pytest.raises(ValidationError) as exc_info:
            UsageRequest(
                model="gpt-4o",
                input_tokens=-1,
                output_tokens=50
            )
        
        assert "greater than or equal to 0" in str(exc_info.value)

    def test_usage_request_negative_output_tokens(self):
        """Test validation with negative output tokens"""
        with pytest.raises(ValidationError) as exc_info:
            UsageRequest(
                model="gpt-4o",
                input_tokens=100,
                output_tokens=-1
            )
        
        assert "greater than or equal to 0" in str(exc_info.value)

    def test_usage_request_excessive_input_tokens(self):
        """Test validation with input tokens exceeding limit"""
        with pytest.raises(ValidationError) as exc_info:
            UsageRequest(
                model="gpt-4o",
                input_tokens=1000001,  # Exceeds default limit
                output_tokens=50
            )
        
        assert "less than or equal to" in str(exc_info.value)

    def test_usage_request_excessive_output_tokens(self):
        """Test validation with output tokens exceeding limit"""
        with pytest.raises(ValidationError) as exc_info:
            UsageRequest(
                model="gpt-4o",
                input_tokens=100,
                output_tokens=1000001  # Exceeds default limit
            )
        
        assert "less than or equal to" in str(exc_info.value)

    def test_usage_request_metadata_none(self):
        """Test that None metadata is handled correctly"""
        request = UsageRequest(
            model="gpt-4o",
            input_tokens=100,
            output_tokens=50,
            metadata=None
        )
        
        assert request.metadata is None

    def test_usage_request_metadata_too_large(self):
        """Test validation with metadata exceeding size limit"""
        # Create metadata that exceeds 1KB when serialized but has <= 10 items
        large_metadata = {f"key_{i}": "x" * 200 for i in range(5)}  # 5 items with large values
        
        with pytest.raises(ValidationError) as exc_info:
            UsageRequest(
                model="gpt-4o",
                input_tokens=100,
                output_tokens=50,
                metadata=large_metadata
            )
        
        assert "Metadata too large" in str(exc_info.value)

    def test_usage_request_metadata_too_many_items(self):
        """Test validation with too many metadata items"""
        many_items_metadata = {f"key_{i}": "value" for i in range(11)}  # Exceeds 10 item limit
        
        with pytest.raises(ValidationError) as exc_info:
            UsageRequest(
                model="gpt-4o",
                input_tokens=100,
                output_tokens=50,
                metadata=many_items_metadata
            )
        
        assert "at most 10" in str(exc_info.value)

    def test_usage_request_zero_tokens(self):
        """Test validation with zero tokens (edge case)"""
        request = UsageRequest(
            model="gpt-4o",
            input_tokens=0,
            output_tokens=0
        )
        
        assert request.input_tokens == 0
        assert request.output_tokens == 0


class TestImpactResponse:
    """Test ImpactResponse model"""

    def test_impact_response_creation(self):
        """Test ImpactResponse model instantiation"""
        response = ImpactResponse(
            model="gpt-4o",
            input_tokens=1000,
            output_tokens=500,
            total_tokens=1500,
            energy_kwh=0.001234,
            gwp_kgco2eq=0.000567,
            calculation_id="calc-abc123",
            timestamp="2024-01-01T12:00:00",
            success=True
        )
        
        assert response.model == "gpt-4o"
        assert response.input_tokens == 1000
        assert response.output_tokens == 500
        assert response.total_tokens == 1500
        assert response.energy_kwh == 0.001234
        assert response.gwp_kgco2eq == 0.000567
        assert response.calculation_id == "calc-abc123"
        assert response.timestamp == "2024-01-01T12:00:00"
        assert response.success is True
        assert response.error is None

    def test_impact_response_with_error(self):
        """Test ImpactResponse with error field"""
        response = ImpactResponse(
            model="unknown-model",
            input_tokens=1000,
            output_tokens=500,
            total_tokens=1500,
            energy_kwh=0.0,
            gwp_kgco2eq=0.0,
            calculation_id="calc-error123",
            timestamp="2024-01-01T12:00:00",
            success=False,
            error="Model not supported"
        )
        
        assert response.success is False
        assert response.error == "Model not supported"
        assert response.energy_kwh == 0.0
        assert response.gwp_kgco2eq == 0.0