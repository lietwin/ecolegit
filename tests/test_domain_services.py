"""Tests for domain services."""

import pytest
import time
from unittest.mock import Mock, patch
from src.domain.services import (
    ImpactCalculationService, CalculationIdService, HealthService,
    ModelInfoService, TestService, EcologitsRepository
)
from src.domain.models import CalculationResult, HealthStatus, ModelInfo, TestResult
# ModelMatch removed - model discovery service was eliminated
from src.config.settings import AppConfig
from src.config.constants import ErrorMessages


class MockEcologitsRepo:
    """Mock EcoLogits repository for testing."""
    
    def __init__(self, supported_models=None, should_fail=False):
        self.supported_models = supported_models or ["gpt-4o", "claude-3-opus"]
        self.should_fail = should_fail
    
    def get_model(self, model_name):
        if self.should_fail:
            raise Exception("Model retrieval failed")
        if model_name in self.supported_models:
            return Mock(name=f"model_{model_name}")
        raise Exception(f"Model {model_name} not found")
    
    def calculate_impacts(self, model, input_tokens, output_tokens):
        if self.should_fail:
            raise Exception("Impact calculation failed")
        
        mock_impacts = Mock()
        mock_impacts.energy.value.mean = 0.001234
        mock_impacts.gwp.value.mean = 0.000567
        return mock_impacts
    
    def get_available_models(self):
        if self.should_fail:
            raise Exception("Failed to get models")
        return {name: Mock() for name in self.supported_models}
    
    def is_model_supported(self, model_name):
        return model_name in self.supported_models


class TestImpactCalculationService:
    """Test ImpactCalculationService."""
    
    @pytest.fixture
    def mock_config(self):
        """Create mock configuration."""
        config = Mock(spec=AppConfig)
        config.model_mappings = {
            "gpt-4o": "gpt-4o-2024-05-13",
            "claude": "claude-3-opus"
        }
        return config
    
    # Model discovery removed - replaced with simple normalization
    
    def test_calculate_impact_success_with_normalization(self, mock_config):
        """Test successful impact calculation with model name normalization."""
        repo = MockEcologitsRepo(supported_models=["gpt-4o-2024-05-13"])
        service = ImpactCalculationService(repo, mock_config)
        
        result = service.calculate_impact("gpt4o", 1000, 500)
        
        assert result.success is True
        assert result.energy_kwh == 0.001234
        assert result.gwp_kgco2eq == 0.000567
        assert result.normalized_model == "gpt-4o-2024-05-13"
    
    def test_calculate_impact_success_fallback_to_config(self, mock_config):
        """Test successful impact calculation fallback to config mappings."""
        repo = MockEcologitsRepo(supported_models=["claude-3-opus"])
        service = ImpactCalculationService(repo, mock_config)
        
        result = service.calculate_impact("claude", 1000, 500)
        
        assert result.success is True
        assert result.energy_kwh == 0.001234
        assert result.normalized_model == "claude-3-opus"
    
    def test_calculate_impact_negative_tokens(self, mock_config):
        """Test impact calculation with negative token counts."""
        repo = MockEcologitsRepo()
        service = ImpactCalculationService(repo, mock_config)
        
        result = service.calculate_impact("gpt-4o", -100, 500)
        
        assert result.success is False
        assert result.error == ErrorMessages.TOKEN_COUNTS_NEGATIVE
        assert result.energy_kwh == 0
        assert result.gwp_kgco2eq == 0
    
    def test_calculate_impact_unsupported_model(self, mock_config):
        """Test impact calculation with unsupported model."""
        repo = MockEcologitsRepo(supported_models=["gpt-4o"])
        service = ImpactCalculationService(repo, mock_config)
        
        result = service.calculate_impact("unknown-model", 1000, 500)
        
        assert result.success is False
        assert "not supported" in result.error
        assert result.energy_kwh == 0
    
    def test_calculate_impact_unknown_model(self, mock_config):
        """Test impact calculation with unknown model (no normalization match)."""
        repo = MockEcologitsRepo(supported_models=["gpt-4o"])
        service = ImpactCalculationService(repo, mock_config)
        
        result = service.calculate_impact("unknown-model", 1000, 500)
        
        assert result.success is False
        assert "not supported" in result.error
    
    def test_calculate_impact_repo_exception(self, mock_config):
        """Test impact calculation when repository throws exception."""
        repo = MockEcologitsRepo(supported_models=["gpt-4o"], should_fail=True)
        service = ImpactCalculationService(repo, mock_config)
        
        result = service.calculate_impact("gpt-4o", 1000, 500)
        
        assert result.success is False
        assert ("not found" in result.error or "not supported" in result.error)
    
    def test_normalize_model_with_typo_correction(self, mock_config):
        """Test model normalization with typo correction."""
        repo = MockEcologitsRepo()
        service = ImpactCalculationService(repo, mock_config)
        
        normalized = service._normalize_model("gpt4o")
        
        assert normalized == "gpt-4o-2024-05-13"  # Uses config mapping
    
    def test_normalize_model_fallback_to_config(self, mock_config):
        """Test model normalization fallback to config mappings."""
        repo = MockEcologitsRepo()
        service = ImpactCalculationService(repo, mock_config)
        
        normalized = service._normalize_model("claude")
        
        assert normalized == "claude-3-opus"
    
    def test_normalize_model_no_mapping(self, mock_config):
        """Test model normalization with no mapping found."""
        repo = MockEcologitsRepo()
        service = ImpactCalculationService(repo, mock_config)
        
        normalized = service._normalize_model("unknown-model")
        
        assert normalized == "unknown-model"  # Returns original


class TestCalculationIdService:
    """Test CalculationIdService."""
    
    def test_generate_id_format(self):
        """Test generated ID format."""
        calc_id = CalculationIdService.generate_id("gpt-4o", 1000, 500)
        
        assert calc_id.startswith("calc-")
        assert len(calc_id) == 21  # "calc-" + 16 chars
    
    def test_generate_id_uniqueness(self):
        """Test that generated IDs are unique."""
        id1 = CalculationIdService.generate_id("gpt-4o", 1000, 500)
        time.sleep(0.001)  # Ensure time difference
        id2 = CalculationIdService.generate_id("gpt-4o", 1000, 500)
        
        assert id1 != id2
    
    def test_generate_id_deterministic_components(self):
        """Test that ID generation includes model and token data."""
        # Mock time to make this deterministic
        with patch('time.time', return_value=1234567890.0):
            calc_id = CalculationIdService.generate_id("test-model", 100, 200)
            
            # Should be deterministic with fixed time - check format
            assert calc_id.startswith("calc-")
            assert len(calc_id) == 21
    
    def test_generate_id_static_method(self):
        """Test that generate_id is a static method."""
        # Should be callable without instance
        calc_id = CalculationIdService.generate_id("model", 100, 200)
        assert isinstance(calc_id, str)


class TestHealthService:
    """Test HealthService."""
    
    def test_init_default_service_name(self):
        """Test HealthService initialization with default name."""
        service = HealthService()
        
        assert service._service_name == "ecologits-webhook"
    
    def test_init_custom_service_name(self):
        """Test HealthService initialization with custom name."""
        service = HealthService("custom-service")
        
        assert service._service_name == "custom-service"
    
    def test_get_health_status(self):
        """Test getting health status."""
        service = HealthService("test-service")
        status = service.get_health_status()
        
        assert isinstance(status, HealthStatus)
        assert status.status == "healthy"
        assert status.service == "test-service"
        assert status.timestamp is not None


class TestModelInfoService:
    """Test ModelInfoService."""
    
    @pytest.fixture
    def mock_config(self):
        """Create mock configuration."""
        config = Mock(spec=AppConfig)
        config.model_mappings = {
            "gpt-4o": "gpt-4o-2024-05-13",
            "claude-3": "claude-3-opus"
        }
        return config
    
    def test_get_model_info_success(self, mock_config):
        """Test successful model info retrieval."""
        repo = MockEcologitsRepo(supported_models=["gpt-4o", "claude-3-opus", "gemini-pro"])
        service = ModelInfoService(repo, mock_config)
        
        info = service.get_model_info()
        
        assert isinstance(info, ModelInfo)
        assert len(info.supported_models) == 2  # From config
        assert "gpt-4o" in info.supported_models
        assert "claude-3" in info.supported_models
        assert info.total_ecologits_models == 3  # From repo
    
    def test_get_model_info_repo_failure(self, mock_config):
        """Test model info when repository fails."""
        repo = MockEcologitsRepo(should_fail=True)
        service = ModelInfoService(repo, mock_config)
        
        # Should handle repo failure gracefully
        info = service.get_model_info()
        
        assert isinstance(info, ModelInfo)
        assert info.total_ecologits_models == 0  # Repo failed, returns 0


class TestTestService:
    """Test TestService."""
    
    @pytest.fixture
    def mock_calculation_service(self):
        """Create mock calculation service."""
        service = Mock()
        service.calculate_impact.return_value = CalculationResult.success_result(
            energy_kwh=0.001234,
            gwp_kgco2eq=0.000567,
            normalized_model="gpt-4o"
        )
        return service
    
    def test_run_test_calculation_success(self, mock_calculation_service):
        """Test successful test calculation."""
        service = TestService(mock_calculation_service)
        
        result = service.run_test_calculation("development")
        
        assert isinstance(result, TestResult)
        assert result.test_model == "gpt-4o"
        assert result.test_tokens == "1000 input + 500 output"
        assert result.energy_kwh == 0.001234
        assert result.gwp_kgco2eq == 0.000567
        assert result.success is True
        assert result.environment == "development"
        
        mock_calculation_service.calculate_impact.assert_called_once_with(
            model="gpt-4o",
            input_tokens=1000,
            output_tokens=500
        )
    
    def test_run_test_calculation_failure(self):
        """Test test calculation when underlying service fails."""
        mock_service = Mock()
        mock_service.calculate_impact.return_value = CalculationResult.error_result("Test error")
        
        service = TestService(mock_service)
        result = service.run_test_calculation("testing")
        
        assert isinstance(result, TestResult)
        assert result.success is False
        assert result.environment == "testing"
        assert result.energy_kwh == 0
        assert result.gwp_kgco2eq == 0


class TestEcologitsRepositoryProtocol:
    """Test EcologitsRepository protocol compliance."""
    
    def test_mock_repo_implements_protocol(self):
        """Test that MockEcologitsRepo implements the protocol."""
        repo = MockEcologitsRepo()
        
        # Should have all required methods
        assert hasattr(repo, 'get_model')
        assert hasattr(repo, 'calculate_impacts')
        assert hasattr(repo, 'get_available_models')
        assert callable(repo.get_model)
        assert callable(repo.calculate_impacts)
        assert callable(repo.get_available_models)
    
    def test_protocol_method_signatures(self):
        """Test protocol method signatures."""
        repo = MockEcologitsRepo()
        
        # Test method calls work
        model = repo.get_model("gpt-4o")
        assert model is not None
        
        impacts = repo.calculate_impacts(model, 100, 50)
        assert impacts is not None
        
        models = repo.get_available_models()
        assert isinstance(models, dict)


class TestServiceIntegration:
    """Integration tests for services working together."""
    
    def test_calculation_service_with_test_service(self):
        """Test calculation service integrated with test service."""
        repo = MockEcologitsRepo(supported_models=["gpt-4o"])
        config = Mock(spec=AppConfig)
        config.model_mappings = {"gpt-4o": "gpt-4o"}
        
        calc_service = ImpactCalculationService(repo, config)
        test_service = TestService(calc_service)
        
        result = test_service.run_test_calculation("integration")
        
        assert result.success is True
        assert result.environment == "integration"
        assert result.energy_kwh > 0
    
    def test_model_info_service_with_calculation_service(self):
        """Test model info service with calculation service."""
        repo = MockEcologitsRepo(supported_models=["gpt-4o", "claude-3-opus"])
        config = Mock(spec=AppConfig)
        config.model_mappings = {"gpt-4o": "gpt-4o", "claude": "claude-3-opus"}
        
        calc_service = ImpactCalculationService(repo, config)
        info_service = ModelInfoService(repo, config)
        
        # Get model info
        info = info_service.get_model_info()
        assert len(info.supported_models) == 2
        
        # Test calculation with supported model
        result = calc_service.calculate_impact("gpt-4o", 100, 50)
        assert result.success is True


class TestServiceErrorHandling:
    """Test error handling across services."""
    
    def test_all_services_handle_repo_failures(self):
        """Test that all services handle repository failures gracefully."""
        failing_repo = MockEcologitsRepo(should_fail=True)
        config = Mock(spec=AppConfig)
        config.model_mappings = {}
        
        # ImpactCalculationService
        calc_service = ImpactCalculationService(failing_repo, config)
        result = calc_service.calculate_impact("test", 100, 50)
        assert result.success is False
        
        # ModelInfoService  
        info_service = ModelInfoService(failing_repo, config)
        info = info_service.get_model_info()
        assert isinstance(info, ModelInfo)  # Should still return valid object
        
        # TestService should propagate the error
        test_service = TestService(calc_service)
        test_result = test_service.run_test_calculation("test")
        assert test_result.success is False


class TestServiceLogging:
    """Test logging in services."""
    
    @patch('src.domain.services.logger')
    def test_calculation_service_logs_errors(self, mock_logger):
        """Test that calculation service logs errors."""
        # Create a repo that supports the model but fails on get_model
        repo = MockEcologitsRepo(supported_models=["test-model"], should_fail=True)
        config = Mock(spec=AppConfig)
        config.model_mappings = {"test-model": "test-model"}
        
        service = ImpactCalculationService(repo, config)
        result = service.calculate_impact("test-model", 100, 50)
        
        assert result.success is False
        mock_logger.error.assert_called()
        # Check that error message contains model name
        error_call = mock_logger.error.call_args[0][0]
        assert "test-model" in error_call
    
    # Model discovery logging test removed since functionality was eliminated