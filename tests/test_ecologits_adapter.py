"""Tests for EcoLogits adapter."""

import pytest
from unittest.mock import Mock, patch, MagicMock
from src.infrastructure.ecologits_adapter import EcologitsAdapter, EcologitsServiceError


class TestEcologitsAdapterInitialization:
    """Test EcoLogits adapter initialization."""
    
    @patch('src.infrastructure.ecologits_adapter.ECOLOGITS_AVAILABLE', True)
    @patch('src.infrastructure.ecologits_adapter.models')
    def test_init_success(self, mock_models):
        """Test successful initialization."""
        adapter = EcologitsAdapter()
        assert adapter._models == mock_models
    
    @patch('src.infrastructure.ecologits_adapter.ECOLOGITS_AVAILABLE', False)
    def test_init_ecologits_not_available(self):
        """Test initialization when EcoLogits is not available."""
        with pytest.raises(EcologitsServiceError, match="EcoLogits library is not installed"):
            EcologitsAdapter()


class TestEcologitsAdapterGetModel:
    """Test get_model method."""
    
    def setup_method(self):
        """Set up test fixtures."""
        with patch('src.infrastructure.ecologits_adapter.ECOLOGITS_AVAILABLE', True), \
             patch('src.infrastructure.ecologits_adapter.models') as mock_models:
            self.mock_models = mock_models
            self.adapter = EcologitsAdapter()
    
    @patch('src.domain.model_utils.detect_provider')
    def test_get_model_success(self, mock_detect_provider):
        """Test successful model retrieval."""
        mock_model = Mock()
        mock_model.name = "gpt-4o"
        mock_model.provider.value = "openai"
        
        mock_detect_provider.return_value = "openai"
        self.mock_models.find_model.return_value = mock_model
        
        result = self.adapter.get_model("gpt-4o")
        
        assert result == mock_model
        mock_detect_provider.assert_called_once_with("gpt-4o")
        self.mock_models.find_model.assert_called_once_with("openai", "gpt-4o")
    
    @patch('src.domain.model_utils.detect_provider')
    def test_get_model_not_found(self, mock_detect_provider):
        """Test getting model that doesn't exist."""
        mock_detect_provider.return_value = "openai"
        self.mock_models.find_model.return_value = None
        
        with pytest.raises(EcologitsServiceError, match="Failed to get model 'unknown-model'"):
            self.adapter.get_model("unknown-model")
    
    @patch('src.domain.model_utils.detect_provider')
    def test_get_model_exception_handling(self, mock_detect_provider):
        """Test exception handling in get_model."""
        mock_detect_provider.return_value = "openai"
        self.mock_models.find_model.side_effect = Exception("Unexpected error")
        
        with pytest.raises(EcologitsServiceError, match="Failed to get model 'gpt-4o'"):
            self.adapter.get_model("gpt-4o")


class TestEcologitsAdapterCalculateImpacts:
    """Test calculate_impacts method."""
    
    def setup_method(self):
        """Set up test fixtures."""
        with patch('src.infrastructure.ecologits_adapter.ECOLOGITS_AVAILABLE', True), \
             patch('src.infrastructure.ecologits_adapter.models'):
            self.adapter = EcologitsAdapter()
    
    @patch('ecologits.tracers.utils.llm_impacts')
    def test_calculate_impacts_success(self, mock_llm_impacts):
        """Test successful impact calculation."""
        mock_model = Mock()
        mock_model.provider.value = "openai"
        mock_model.name = "gpt-4o"
        
        mock_impacts = Mock()
        mock_impacts.energy.value = 0.001234
        mock_impacts.gwp.value = 0.000567
        mock_llm_impacts.return_value = mock_impacts
        
        result = self.adapter.calculate_impacts(mock_model, 1000, 500)
        
        assert result == mock_impacts
        mock_llm_impacts.assert_called_once_with(
            provider="openai",
            model_name="gpt-4o",
            output_token_count=500,
            request_latency=1.0
        )
    
    @patch('ecologits.tracers.utils.llm_impacts')
    def test_calculate_impacts_exception(self, mock_llm_impacts):
        """Test exception handling in calculate_impacts."""
        mock_model = Mock()
        mock_model.provider.value = "openai"
        mock_model.name = "gpt-4o"
        mock_llm_impacts.side_effect = Exception("Calculation failed")
        
        with pytest.raises(EcologitsServiceError, match="Failed to calculate environmental impacts"):
            self.adapter.calculate_impacts(mock_model, 1000, 500)


class TestEcologitsAdapterGetAvailableModels:
    """Test get_available_models method."""
    
    def setup_method(self):
        """Set up test fixtures."""
        with patch('src.infrastructure.ecologits_adapter.ECOLOGITS_AVAILABLE', True), \
             patch('src.infrastructure.ecologits_adapter.models') as mock_models:
            self.mock_models = mock_models
            self.adapter = EcologitsAdapter()
    
    def test_get_available_models_success(self):
        """Test successful model listing."""
        mock_model1 = Mock()
        mock_model1.name = "gpt-4o"
        mock_model2 = Mock()
        mock_model2.name = "claude-3-opus"
        
        mock_model_list = [mock_model1, mock_model2]
        self.mock_models.list_models.return_value = mock_model_list
        
        result = self.adapter.get_available_models()
        
        expected = {
            "gpt-4o": mock_model1,
            "claude-3-opus": mock_model2
        }
        assert result == expected
        self.mock_models.list_models.assert_called_once()
    
    def test_get_available_models_exception(self):
        """Test exception handling in get_available_models."""
        self.mock_models.list_models.side_effect = Exception("API error")
        
        result = self.adapter.get_available_models()
        
        assert result == {}


class TestEcologitsAdapterIsModelSupported:
    """Test is_model_supported method."""
    
    def setup_method(self):
        """Set up test fixtures."""
        with patch('src.infrastructure.ecologits_adapter.ECOLOGITS_AVAILABLE', True), \
             patch('src.infrastructure.ecologits_adapter.models') as mock_models:
            self.mock_models = mock_models
            self.adapter = EcologitsAdapter()
    
    @patch('src.domain.model_utils.detect_provider')
    def test_is_model_supported_true(self, mock_detect_provider):
        """Test model support check returns True."""
        mock_model = Mock()
        mock_detect_provider.return_value = "openai"
        self.mock_models.find_model.return_value = mock_model
        
        result = self.adapter.is_model_supported('gpt-4o')
        
        assert result is True
        mock_detect_provider.assert_called_once_with('gpt-4o')
        self.mock_models.find_model.assert_called_once_with('openai', 'gpt-4o')
    
    @patch('src.domain.model_utils.detect_provider')
    def test_is_model_supported_false(self, mock_detect_provider):
        """Test model support check returns False."""
        mock_detect_provider.return_value = "openai"
        self.mock_models.find_model.return_value = None
        
        result = self.adapter.is_model_supported('unknown-model')
        
        assert result is False
    
    @patch('src.domain.model_utils.detect_provider')
    def test_is_model_supported_exception(self, mock_detect_provider):
        """Test exception handling in is_model_supported."""
        mock_detect_provider.side_effect = Exception("Provider detection failed")
        
        result = self.adapter.is_model_supported('gpt-4o')
        
        assert result is False


class TestEcologitsServiceError:
    """Test EcologitsServiceError exception."""
    
    def test_error_creation(self):
        """Test creating EcologitsServiceError."""
        error = EcologitsServiceError("Test error message")
        
        assert str(error) == "Test error message"
        assert isinstance(error, Exception)
    
    def test_error_inheritance(self):
        """Test that EcologitsServiceError inherits from Exception."""
        assert issubclass(EcologitsServiceError, Exception)


class TestEcologitsAdapterIntegration:
    """Integration tests for EcoLogits adapter."""
    
    @patch('src.domain.model_utils.detect_provider')
    @patch('ecologits.tracers.utils.llm_impacts')
    def test_full_workflow_success(self, mock_llm_impacts, mock_detect_provider):
        """Test full workflow from model discovery to calculation."""
        with patch('src.infrastructure.ecologits_adapter.ECOLOGITS_AVAILABLE', True), \
             patch('src.infrastructure.ecologits_adapter.models') as mock_models:
            
            # Setup mocks
            mock_model = Mock()
            mock_model.name = "gpt-4o"
            mock_model.provider.value = "openai"
            
            mock_detect_provider.return_value = "openai"
            mock_models.find_model.return_value = mock_model
            
            mock_impacts = Mock()
            mock_impacts.energy.value = 0.001234
            mock_impacts.gwp.value = 0.000567
            mock_llm_impacts.return_value = mock_impacts
            
            # Create adapter
            adapter = EcologitsAdapter()
            
            # Test model support
            assert adapter.is_model_supported('gpt-4o') is True
            
            # Test model retrieval
            model = adapter.get_model('gpt-4o')
            assert model == mock_model
            
            # Test impact calculation
            impacts = adapter.calculate_impacts(model, 1000, 500)
            assert impacts == mock_impacts
    
    @patch('src.domain.model_utils.detect_provider')
    def test_error_propagation_workflow(self, mock_detect_provider):
        """Test error propagation through workflow."""
        with patch('src.infrastructure.ecologits_adapter.ECOLOGITS_AVAILABLE', True), \
             patch('src.infrastructure.ecologits_adapter.models') as mock_models:
            
            # Setup model to fail
            mock_detect_provider.return_value = "openai"
            mock_models.find_model.side_effect = Exception("Connection failed")
            
            adapter = EcologitsAdapter()
            
            # Should propagate as EcologitsServiceError
            with pytest.raises(EcologitsServiceError):
                adapter.get_model('gpt-4o')


class TestEcologitsAdapterLogging:
    """Test logging in EcoLogits adapter."""
    
    @patch('src.infrastructure.ecologits_adapter.logger')
    def test_initialization_logging(self, mock_logger):
        """Test logging during initialization."""
        with patch('src.infrastructure.ecologits_adapter.ECOLOGITS_AVAILABLE', True), \
             patch('src.infrastructure.ecologits_adapter.models'):
            
            EcologitsAdapter()
            
            mock_logger.info.assert_called_with("EcologitsAdapter initialized")
    
    @patch('src.infrastructure.ecologits_adapter.logger')
    @patch('src.domain.model_utils.detect_provider')
    def test_error_logging_in_get_model(self, mock_detect_provider, mock_logger):
        """Test error logging in get_model."""
        with patch('src.infrastructure.ecologits_adapter.ECOLOGITS_AVAILABLE', True), \
             patch('src.infrastructure.ecologits_adapter.models') as mock_models:
            
            mock_detect_provider.return_value = "openai"
            mock_models.find_model.side_effect = Exception("Test error")
            adapter = EcologitsAdapter()
            
            with pytest.raises(EcologitsServiceError):
                adapter.get_model('test-model')
            
            mock_logger.error.assert_called_with("Error getting model 'test-model': Test error")
    
    @patch('src.infrastructure.ecologits_adapter.logger')
    @patch('ecologits.tracers.utils.llm_impacts')
    def test_debug_logging_in_calculate_impacts(self, mock_llm_impacts, mock_logger):
        """Test debug logging in calculate_impacts."""
        with patch('src.infrastructure.ecologits_adapter.ECOLOGITS_AVAILABLE', True), \
             patch('src.infrastructure.ecologits_adapter.models'):
            
            mock_impacts = Mock()
            mock_impacts.energy.value = 0.001234
            mock_impacts.gwp.value = 0.000567
            mock_llm_impacts.return_value = mock_impacts
            
            adapter = EcologitsAdapter()
            mock_model = Mock()
            mock_model.provider.value = "openai"
            mock_model.name = "gpt-4o"
            
            adapter.calculate_impacts(mock_model, 1000, 500)
            
            mock_logger.debug.assert_called_with(
                "Impact calculation successful: energy=0.001234, gwp=0.000567"
            )