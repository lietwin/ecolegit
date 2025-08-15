"""Tests for dependency injection failure paths - CRITICAL for service startup reliability."""

import pytest
from unittest.mock import Mock, patch, MagicMock
from fastapi import HTTPException

from src.api.dependencies import (
    DependencyContainer,
    initialize_dependencies,
    get_app_config,
    get_security_manager,
    get_impact_calculation_service,
    get_calculation_id_service,
    get_health_service,
    get_model_info_service,
    get_test_service,
    verify_authentication,
    _container
)
from src.config.settings import AppConfig, SecurityConfig
from src.infrastructure.security import SecurityManager
from src.domain.services import ImpactCalculationService


class TestDependencyContainer:
    """Test DependencyContainer initialization and failure scenarios."""
    
    def test_container_successful_initialization(self):
        """Test successful container initialization with valid config."""
        config = AppConfig()
        
        with patch('src.api.dependencies.EcologitsAdapter') as mock_adapter:
            mock_adapter.return_value = Mock()
            
            container = DependencyContainer(config)
            
            assert container.config == config
            assert container.security_manager is not None
            assert container.ecologits_adapter is not None
            assert container.impact_service is not None
            assert container.calculation_id_service is not None
            assert container.health_service is not None
            assert container.model_info_service is not None
            assert container.test_service is not None
    
    def test_container_ecologits_adapter_failure(self):
        """Test container initialization when EcologitsAdapter fails."""
        config = AppConfig()
        
        with patch('src.api.dependencies.EcologitsAdapter') as mock_adapter:
            mock_adapter.side_effect = Exception("EcoLogits initialization failed")
            
            with pytest.raises(Exception, match="EcoLogits initialization failed"):
                DependencyContainer(config)
    
    def test_container_security_manager_failure(self):
        """Test container initialization when security manager creation fails."""
        config = AppConfig()
        
        with patch('src.api.dependencies.EcologitsAdapter') as mock_adapter, \
             patch('src.api.dependencies.create_security_manager') as mock_security:
            
            mock_adapter.return_value = Mock()
            mock_security.side_effect = Exception("Security manager creation failed")
            
            with pytest.raises(Exception, match="Security manager creation failed"):
                DependencyContainer(config)
    
    def test_container_service_initialization_failure(self):
        """Test container initialization when service creation fails."""
        config = AppConfig()
        
        with patch('src.api.dependencies.EcologitsAdapter') as mock_adapter, \
             patch('src.api.dependencies.ImpactCalculationService') as mock_service:
            
            mock_adapter.return_value = Mock()
            mock_service.side_effect = Exception("Impact service initialization failed")
            
            with pytest.raises(Exception, match="Impact service initialization failed"):
                DependencyContainer(config)


class TestInitializeDependencies:
    """Test global dependency initialization."""
    
    def teardown_method(self):
        """Reset global container after each test."""
        import src.api.dependencies
        src.api.dependencies._container = None
    
    def test_initialize_dependencies_success(self):
        """Test successful dependency initialization."""
        config = AppConfig()
        
        with patch('src.api.dependencies.DependencyContainer') as mock_container_class:
            mock_container = Mock()
            mock_container_class.return_value = mock_container
            
            initialize_dependencies(config)
            
            mock_container_class.assert_called_once_with(config)
            # Verify global container is set
            import src.api.dependencies
            assert src.api.dependencies._container == mock_container
    
    def test_initialize_dependencies_failure(self):
        """Test dependency initialization failure propagation."""
        config = AppConfig()
        
        with patch('src.api.dependencies.DependencyContainer') as mock_container_class:
            mock_container_class.side_effect = Exception("Container initialization failed")
            
            with pytest.raises(Exception, match="Container initialization failed"):
                initialize_dependencies(config)
            
            # Verify global container remains None on failure
            import src.api.dependencies
            assert src.api.dependencies._container is None


class TestDependencyGetters:
    """Test dependency getter functions and their failure modes."""
    
    def teardown_method(self):
        """Reset global container after each test."""
        import src.api.dependencies
        src.api.dependencies._container = None
    
    def test_get_app_config_success(self):
        """Test successful config retrieval."""
        config = AppConfig()
        
        with patch('src.api.dependencies._container') as mock_container:
            mock_container.config = config
            
            result = get_app_config()
            
            assert result == config
    
    def test_get_app_config_container_not_initialized(self):
        """Test config retrieval when container is not initialized."""
        # Container is None by default in teardown
        
        with pytest.raises(RuntimeError, match="Dependencies not initialized"):
            get_app_config()
    
    def test_get_security_manager_success(self):
        """Test successful security manager retrieval."""
        mock_security_manager = Mock(spec=SecurityManager)
        
        with patch('src.api.dependencies._container') as mock_container:
            mock_container.security_manager = mock_security_manager
            
            result = get_security_manager()
            
            assert result == mock_security_manager
    
    def test_get_security_manager_container_not_initialized(self):
        """Test security manager retrieval when container is not initialized."""
        with pytest.raises(RuntimeError, match="Dependencies not initialized"):
            get_security_manager()
    
    def test_get_impact_calculation_service_success(self):
        """Test successful impact service retrieval."""
        mock_service = Mock(spec=ImpactCalculationService)
        
        with patch('src.api.dependencies._container') as mock_container:
            mock_container.impact_service = mock_service
            
            result = get_impact_calculation_service()
            
            assert result == mock_service
    
    def test_get_impact_calculation_service_container_not_initialized(self):
        """Test impact service retrieval when container is not initialized."""
        with pytest.raises(RuntimeError, match="Dependencies not initialized"):
            get_impact_calculation_service()
    
    def test_get_calculation_id_service_container_not_initialized(self):
        """Test calculation ID service retrieval when container is not initialized."""
        with pytest.raises(RuntimeError, match="Dependencies not initialized"):
            get_calculation_id_service()
    
    def test_get_health_service_container_not_initialized(self):
        """Test health service retrieval when container is not initialized."""
        with pytest.raises(RuntimeError, match="Dependencies not initialized"):
            get_health_service()
    
    def test_get_model_info_service_container_not_initialized(self):
        """Test model info service retrieval when container is not initialized."""
        with pytest.raises(RuntimeError, match="Dependencies not initialized"):
            get_model_info_service()
    
    def test_get_test_service_container_not_initialized(self):
        """Test test service retrieval when container is not initialized."""
        with pytest.raises(RuntimeError, match="Dependencies not initialized"):
            get_test_service()


class TestVerifyAuthentication:
    """Test authentication verification dependency."""
    
    def teardown_method(self):
        """Reset global container after each test."""
        import src.api.dependencies
        src.api.dependencies._container = None
    
    def test_verify_authentication_success(self):
        """Test successful authentication verification."""
        mock_security_manager = Mock()
        mock_security_manager.verify_authentication.return_value = True
        
        with patch('src.api.dependencies._container') as mock_container:
            mock_container.security_manager = mock_security_manager
            
            from fastapi.security import HTTPAuthorizationCredentials
            credentials = HTTPAuthorizationCredentials(scheme="Bearer", credentials="test-key")
            
            result = verify_authentication(credentials, mock_security_manager)
            
            assert result is True
            mock_security_manager.verify_authentication.assert_called_once_with(credentials)
    
    def test_verify_authentication_failure_propagates_http_exception(self):
        """Test that authentication failures propagate HTTPException."""
        mock_security_manager = Mock()
        mock_security_manager.verify_authentication.side_effect = HTTPException(
            status_code=401,
            detail="Invalid credentials"
        )
        
        from fastapi.security import HTTPAuthorizationCredentials
        credentials = HTTPAuthorizationCredentials(scheme="Bearer", credentials="bad-key")
        
        with pytest.raises(HTTPException) as exc_info:
            verify_authentication(credentials, mock_security_manager)
        
        assert exc_info.value.status_code == 401
        assert exc_info.value.detail == "Invalid credentials"


class TestDependencyIntegrationFailures:
    """Test integration scenarios where multiple dependencies fail."""
    
    def teardown_method(self):
        """Reset global container after each test."""
        import src.api.dependencies
        src.api.dependencies._container = None
    
    def test_cascading_dependency_failure(self):
        """Test that failure in one dependency prevents others from initializing."""
        config = AppConfig()
        
        # Mock EcologitsAdapter to fail
        with patch('src.api.dependencies.EcologitsAdapter') as mock_adapter:
            mock_adapter.side_effect = Exception("EcoLogits connection failed")
            
            # Attempt to initialize - should fail early
            with pytest.raises(Exception, match="EcoLogits connection failed"):
                initialize_dependencies(config)
            
            # Verify no services are available
            with pytest.raises(RuntimeError, match="Dependencies not initialized"):
                get_impact_calculation_service()
    
    def test_partial_initialization_cleanup(self):
        """Test that partial initialization doesn't leave system in inconsistent state."""
        config = AppConfig()
        
        # Mock successful adapter but failing service
        with patch('src.api.dependencies.EcologitsAdapter') as mock_adapter, \
             patch('src.api.dependencies.ImpactCalculationService') as mock_service:
            
            mock_adapter.return_value = Mock()
            mock_service.side_effect = Exception("Service initialization failed")
            
            with pytest.raises(Exception, match="Service initialization failed"):
                initialize_dependencies(config)
            
            # Verify container is not set (clean failure)
            import src.api.dependencies
            assert src.api.dependencies._container is None
    
    def test_double_initialization_safety(self):
        """Test that re-initializing dependencies works correctly."""
        config1 = AppConfig(api_key="key1")
        config2 = AppConfig(api_key="key2")
        
        with patch('src.api.dependencies.DependencyContainer') as mock_container_class:
            # First initialization
            mock_container1 = Mock()
            mock_container1.config = config1
            mock_container_class.return_value = mock_container1
            
            initialize_dependencies(config1)
            import src.api.dependencies
            assert src.api.dependencies._container == mock_container1
            
            # Second initialization should replace first
            mock_container2 = Mock()
            mock_container2.config = config2
            mock_container_class.return_value = mock_container2
            
            initialize_dependencies(config2)
            assert src.api.dependencies._container == mock_container2


class TestRealWorldFailureScenarios:
    """Test real-world failure scenarios that could occur in production."""
    
    def teardown_method(self):
        """Reset global container after each test."""
        import src.api.dependencies
        src.api.dependencies._container = None
    
    def test_ecologits_import_failure_scenario(self):
        """Test scenario where EcoLogits library is not available."""
        config = AppConfig()
        
        # Simulate ImportError that would occur if ecologits package is missing
        with patch('src.api.dependencies.EcologitsAdapter') as mock_adapter:
            mock_adapter.side_effect = ImportError("No module named 'ecologits'")
            
            with pytest.raises(ImportError, match="No module named 'ecologits'"):
                initialize_dependencies(config)
    
    def test_configuration_validation_failure(self):
        """Test scenario where configuration validation fails during service creation."""
        # Create config with invalid settings that might cause service initialization to fail
        config = AppConfig()
        
        with patch('src.api.dependencies.EcologitsAdapter') as mock_adapter, \
             patch('src.api.dependencies.create_security_manager') as mock_security:
            
            mock_adapter.return_value = Mock()
            # Simulate security manager rejecting invalid config
            mock_security.side_effect = ValueError("Invalid security configuration")
            
            with pytest.raises(ValueError, match="Invalid security configuration"):
                initialize_dependencies(config)
    
    def test_network_failure_during_initialization(self):
        """Test scenario where network issues affect service initialization."""
        config = AppConfig()
        
        with patch('src.api.dependencies.EcologitsAdapter') as mock_adapter:
            # Simulate network timeout during EcoLogits initialization
            mock_adapter.side_effect = TimeoutError("Connection to EcoLogits timed out")
            
            with pytest.raises(TimeoutError, match="Connection to EcoLogits timed out"):
                initialize_dependencies(config)
    
    def test_memory_exhaustion_during_initialization(self):
        """Test scenario where memory issues affect initialization."""
        config = AppConfig()
        
        with patch('src.api.dependencies.EcologitsAdapter') as mock_adapter:
            # Simulate memory error
            mock_adapter.side_effect = MemoryError("Cannot allocate memory")
            
            with pytest.raises(MemoryError, match="Cannot allocate memory"):
                initialize_dependencies(config)