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
        mock_models.some_model = Mock()
        
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
    
    def test_get_model_with_get_method(self):
        """Test getting model when models has get method."""
        mock_model = Mock()
        self.mock_models.get.return_value = mock_model
        
        result = self.adapter.get_model("gpt-4o")
        
        assert result == mock_model
        self.mock_models.get.assert_called_once_with("gpt-4o")
    
    def test_get_model_with_attribute_access(self):
        """Test getting model via attribute access."""
        mock_model = Mock()
        
        # Mock hasattr and getattr
        def mock_hasattr(obj, attr):
            if attr == 'get':
                return False
            elif attr == 'gpt-4o':
                return True
            return False
        
        def mock_getattr(obj, attr, default=None):
            if attr == 'gpt-4o':
                return mock_model
            return default
        
        with patch('builtins.hasattr', side_effect=mock_hasattr), \
             patch('builtins.getattr', side_effect=mock_getattr):
            
            result = self.adapter.get_model("gpt-4o")
            
            assert result == mock_model
    
    def test_get_model_with_internal_models_dict(self):
        """Test getting model from internal _models dict."""
        mock_model = Mock()
        
        def mock_hasattr(obj, attr):
            if attr in ['get', 'gpt-4o']:
                return False
            elif attr == '_models':
                return True
            return False
        
        def mock_getattr(obj, attr, default=None):
            if attr == '_models':
                return {'gpt-4o': mock_model}
            return default
        
        with patch('builtins.hasattr', side_effect=mock_hasattr), \
             patch('builtins.getattr', side_effect=mock_getattr):
            
            result = self.adapter.get_model("gpt-4o")
            
            assert result == mock_model
    
    def test_get_model_with_models_attribute(self):
        """Test getting model from models attribute."""
        mock_model = Mock()
        
        def mock_hasattr(obj, attr):
            if attr in ['get', 'gpt-4o', '_models']:
                return False
            elif attr == 'models':
                return True
            return False
        
        def mock_getattr(obj, attr, default=None):
            if attr == 'models':
                return {'gpt-4o': mock_model}
            return default
        
        with patch('builtins.hasattr', side_effect=mock_hasattr), \
             patch('builtins.getattr', side_effect=mock_getattr):
            
            result = self.adapter.get_model("gpt-4o")
            
            assert result == mock_model
    
    def test_get_model_not_found(self):
        """Test getting model that doesn't exist."""
        def mock_hasattr(obj, attr):
            return False
        
        with patch('builtins.hasattr', side_effect=mock_hasattr):
            with pytest.raises(EcologitsServiceError, match="Model 'unknown-model' not found"):
                self.adapter.get_model("unknown-model")
    
    def test_get_model_exception_handling(self):
        """Test exception handling in get_model."""
        self.mock_models.get.side_effect = Exception("Unexpected error")
        
        with pytest.raises(EcologitsServiceError, match="Failed to get model 'gpt-4o'"):
            self.adapter.get_model("gpt-4o")


class TestEcologitsAdapterCalculateImpacts:
    """Test calculate_impacts method."""
    
    def setup_method(self):
        """Set up test fixtures."""
        with patch('src.infrastructure.ecologits_adapter.ECOLOGITS_AVAILABLE', True), \
             patch('src.infrastructure.ecologits_adapter.models'):
            self.adapter = EcologitsAdapter()
    
    @patch('src.infrastructure.ecologits_adapter.Impacts')
    def test_calculate_impacts_success(self, mock_impacts_class):
        """Test successful impact calculation."""
        mock_model = Mock()
        mock_impacts = Mock()
        mock_impacts.energy.value = 0.001234
        mock_impacts.gwp.value = 0.000567
        
        mock_impacts_class.from_model_and_tokens.return_value = mock_impacts
        
        result = self.adapter.calculate_impacts(mock_model, 1000, 500)
        
        assert result == mock_impacts
        mock_impacts_class.from_model_and_tokens.assert_called_once_with(
            model=mock_model,
            input_tokens=1000,
            output_tokens=500
        )
    
    @patch('src.infrastructure.ecologits_adapter.Impacts')
    def test_calculate_impacts_exception(self, mock_impacts_class):
        """Test exception handling in calculate_impacts."""
        mock_model = Mock()
        mock_impacts_class.from_model_and_tokens.side_effect = Exception("Calculation failed")
        
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
    
    def test_get_available_models_with_private_models(self):
        """Test getting models from _models attribute."""
        mock_models_dict = {
            'gpt-4o': Mock(),
            'claude-3-opus': Mock()
        }
        
        def mock_hasattr(obj, attr):
            if attr == '_models':
                return True
            return False
        
        def mock_getattr(obj, attr, default=None):
            if attr == '_models':
                mock_obj = Mock()
                mock_obj.items.return_value = mock_models_dict.items()
                return mock_obj
            return default
        
        with patch('builtins.hasattr', side_effect=mock_hasattr), \
             patch('builtins.getattr', side_effect=mock_getattr):
            
            result = self.adapter.get_available_models()
            
            assert result == mock_models_dict
    
    def test_get_available_models_with_models_attribute(self):
        """Test getting models from models attribute."""
        mock_models_dict = {
            'gpt-4o': Mock(),
            'claude-3-opus': Mock()
        }
        
        def mock_hasattr(obj, attr):
            if attr == '_models':
                return False
            elif attr == 'models':
                return True
            return False
        
        def mock_getattr(obj, attr, default=None):
            if attr == 'models':
                mock_obj = Mock()
                mock_obj.items.return_value = mock_models_dict.items()
                return mock_obj
            return default
        
        with patch('builtins.hasattr', side_effect=mock_hasattr), \
             patch('builtins.getattr', side_effect=mock_getattr):
            
            result = self.adapter.get_available_models()
            
            assert result == mock_models_dict
    
    def test_get_available_models_via_dir(self):
        """Test getting models via directory inspection."""
        mock_model = Mock()
        
        def mock_hasattr(obj, attr):
            return False
        
        def mock_dir(obj):
            return ['gpt_4o', 'claude_3_opus', '_private_attr', '__dunder__', 'some_method']
        
        def mock_getattr(obj, attr, default=None):
            if attr in ['gpt_4o', 'claude_3_opus']:
                return mock_model
            elif attr == 'some_method':
                return lambda: None  # Callable
            return default
        
        def mock_callable(obj):
            return hasattr(obj, '__call__')
        
        with patch('builtins.hasattr', side_effect=mock_hasattr), \
             patch('builtins.dir', side_effect=mock_dir), \
             patch('builtins.getattr', side_effect=mock_getattr), \
             patch('builtins.callable', side_effect=mock_callable):
            
            result = self.adapter.get_available_models()
            
            expected = {'gpt_4o': mock_model, 'claude_3_opus': mock_model}
            assert result == expected
    
    def test_get_available_models_exception(self):
        """Test exception handling in get_available_models."""
        def mock_hasattr(obj, attr):
            raise Exception("Unexpected error")
        
        with patch('builtins.hasattr', side_effect=mock_hasattr):
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
    
    def test_is_model_supported_via_hasattr(self):
        """Test model support check via hasattr."""
        def mock_hasattr(obj, attr):
            return attr == 'gpt-4o'
        
        def mock_getattr(obj, attr, default=None):
            if attr == 'gpt-4o':
                return Mock()  # Non-None value
            return default
        
        with patch('builtins.hasattr', side_effect=mock_hasattr), \
             patch('builtins.getattr', side_effect=mock_getattr):
            
            assert self.adapter.is_model_supported('gpt-4o') is True
            assert self.adapter.is_model_supported('unknown-model') is False
    
    def test_is_model_supported_via_private_models(self):
        """Test model support check via _models.__contains__."""
        def mock_hasattr(obj, attr):
            if attr == 'gpt-4o':
                return False
            elif attr == '_models':
                return True
            elif attr == '__contains__':
                return True
            return False
        
        def mock_getattr(obj, attr, default=None):
            if attr == '_models':
                mock_obj = Mock()
                mock_obj.__contains__ = Mock(return_value=True)
                return mock_obj
            return default
        
        with patch('builtins.hasattr', side_effect=mock_hasattr), \
             patch('builtins.getattr', side_effect=mock_getattr):
            
            result = self.adapter.is_model_supported('gpt-4o')
            
            assert result is True
    
    def test_is_model_supported_via_models_attribute(self):
        """Test model support check via models.__contains__."""
        def mock_hasattr(obj, attr):
            if attr in ['gpt-4o', '_models']:
                return False
            elif attr == 'models':
                return True
            elif attr == '__contains__':
                return True
            return False
        
        def mock_getattr(obj, attr, default=None):
            if attr == 'models':
                mock_obj = Mock()
                mock_obj.__contains__ = Mock(return_value=True)
                return mock_obj
            return default
        
        with patch('builtins.hasattr', side_effect=mock_hasattr), \
             patch('builtins.getattr', side_effect=mock_getattr):
            
            result = self.adapter.is_model_supported('gpt-4o')
            
            assert result is True
    
    def test_is_model_supported_fallback(self):
        """Test model support fallback when no method works."""
        def mock_hasattr(obj, attr):
            return False
        
        with patch('builtins.hasattr', side_effect=mock_hasattr):
            result = self.adapter.is_model_supported('gpt-4o')
            
            assert result is False
    
    def test_is_model_supported_exception(self):
        """Test exception handling in is_model_supported."""
        def mock_hasattr(obj, attr):
            raise Exception("Unexpected error")
        
        with patch('builtins.hasattr', side_effect=mock_hasattr):
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
    
    def test_full_workflow_success(self):
        """Test full workflow from model discovery to calculation."""
        with patch('src.infrastructure.ecologits_adapter.ECOLOGITS_AVAILABLE', True), \
             patch('src.infrastructure.ecologits_adapter.models') as mock_models, \
             patch('src.infrastructure.ecologits_adapter.Impacts') as mock_impacts_class:
            
            # Setup mocks
            mock_model = Mock()
            mock_models.get.return_value = mock_model
            
            mock_impacts = Mock()
            mock_impacts.energy.value = 0.001234
            mock_impacts.gwp.value = 0.000567
            mock_impacts_class.from_model_and_tokens.return_value = mock_impacts
            
            # Create adapter
            adapter = EcologitsAdapter()
            
            # Test model support
            adapter._models = mock_models
            with patch.object(adapter, 'is_model_supported', return_value=True):
                assert adapter.is_model_supported('gpt-4o') is True
            
            # Test model retrieval
            model = adapter.get_model('gpt-4o')
            assert model == mock_model
            
            # Test impact calculation
            impacts = adapter.calculate_impacts(model, 1000, 500)
            assert impacts == mock_impacts
    
    def test_error_propagation_workflow(self):
        """Test error propagation through workflow."""
        with patch('src.infrastructure.ecologits_adapter.ECOLOGITS_AVAILABLE', True), \
             patch('src.infrastructure.ecologits_adapter.models') as mock_models:
            
            # Setup model to fail
            mock_models.get.side_effect = Exception("Connection failed")
            
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
    def test_error_logging_in_get_model(self, mock_logger):
        """Test error logging in get_model."""
        with patch('src.infrastructure.ecologits_adapter.ECOLOGITS_AVAILABLE', True), \
             patch('src.infrastructure.ecologits_adapter.models') as mock_models:
            
            mock_models.get.side_effect = Exception("Test error")
            adapter = EcologitsAdapter()
            
            with pytest.raises(EcologitsServiceError):
                adapter.get_model('test-model')
            
            mock_logger.error.assert_called_with("Error getting model 'test-model': Test error")
    
    @patch('src.infrastructure.ecologits_adapter.logger')
    def test_debug_logging_in_calculate_impacts(self, mock_logger):
        """Test debug logging in calculate_impacts."""
        with patch('src.infrastructure.ecologits_adapter.ECOLOGITS_AVAILABLE', True), \
             patch('src.infrastructure.ecologits_adapter.models'), \
             patch('src.infrastructure.ecologits_adapter.Impacts') as mock_impacts_class:
            
            mock_impacts = Mock()
            mock_impacts.energy.value = 0.001234
            mock_impacts.gwp.value = 0.000567
            mock_impacts_class.from_model_and_tokens.return_value = mock_impacts
            
            adapter = EcologitsAdapter()
            mock_model = Mock()
            
            adapter.calculate_impacts(mock_model, 1000, 500)
            
            mock_logger.debug.assert_called_with(
                "Impact calculation successful: energy=0.001234, gwp=0.000567"
            )