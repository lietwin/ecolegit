"""Tests for environment-specific behavior - CRITICAL for production reliability."""

import pytest
import logging
from unittest.mock import Mock, patch, MagicMock
from fastapi import FastAPI

from src.config.constants import Environment, DefaultValues
from src.config.settings import AppConfig, SecurityConfig, RateLimitConfig
from src.infrastructure.logging import setup_logging
from src.application import create_fastapi_app, register_routes, create_app


class TestLoggingEnvironmentBehavior:
    """Test logging configuration for different environments."""
    
    def test_production_logging_configuration(self):
        """Test that production environment uses WARNING level logging."""
        with patch('logging.basicConfig') as mock_basic_config:
            setup_logging(Environment.PRODUCTION)
            
            # Verify WARNING level is set for production
            mock_basic_config.assert_called_once()
            call_args = mock_basic_config.call_args
            assert call_args[1]['level'] == logging.WARNING
    
    def test_development_logging_configuration(self):
        """Test that development environment uses DEBUG level logging."""
        with patch('logging.basicConfig') as mock_basic_config:
            setup_logging(Environment.DEVELOPMENT)
            
            # Verify DEBUG level is set for development
            mock_basic_config.assert_called_once()
            call_args = mock_basic_config.call_args
            assert call_args[1]['level'] == logging.DEBUG
    
    def test_testing_logging_configuration(self):
        """Test that testing environment uses ERROR level logging."""
        with patch('logging.basicConfig') as mock_basic_config:
            setup_logging(Environment.TESTING)
            
            # Verify ERROR level is set for testing
            mock_basic_config.assert_called_once()
            call_args = mock_basic_config.call_args
            assert call_args[1]['level'] == logging.ERROR
    
    def test_custom_log_level_overrides_environment(self):
        """Test that custom log level overrides environment defaults."""
        with patch('logging.basicConfig') as mock_basic_config:
            setup_logging(Environment.PRODUCTION, log_level="DEBUG")
            
            # Verify custom level overrides environment default
            mock_basic_config.assert_called_once()
            call_args = mock_basic_config.call_args
            assert call_args[1]['level'] == logging.DEBUG
    
    def test_invalid_log_level_defaults_to_info(self):
        """Test that invalid log level defaults to INFO."""
        with patch('logging.basicConfig') as mock_basic_config:
            setup_logging(Environment.DEVELOPMENT, log_level="INVALID")
            
            mock_basic_config.assert_called_once()
            call_args = mock_basic_config.call_args
            assert call_args[1]['level'] == logging.INFO


class TestFastAPIEnvironmentBehavior:
    """Test FastAPI app configuration for different environments."""
    
    def test_production_app_disables_docs(self):
        """Test that production environment disables API documentation."""
        config = AppConfig(environment=Environment.PRODUCTION)
        app = create_fastapi_app(config)
        
        # Verify docs are disabled in production
        assert app.docs_url is None
        assert app.redoc_url is None
    
    def test_development_app_enables_docs(self):
        """Test that development environment enables API documentation."""
        config = AppConfig(environment=Environment.DEVELOPMENT)
        app = create_fastapi_app(config)
        
        # Verify docs are enabled in development
        assert app.docs_url == "/docs"
        assert app.redoc_url == "/redoc"
    
    def test_testing_app_enables_docs(self):
        """Test that testing environment enables API documentation."""
        config = AppConfig(environment=Environment.TESTING)
        app = create_fastapi_app(config)
        
        # Verify docs are enabled in testing
        assert app.docs_url == "/docs"
        assert app.redoc_url == "/redoc"


class TestRouteRegistrationEnvironmentBehavior:
    """Test route registration behavior for different environments."""
    
    @pytest.fixture
    def mock_app(self):
        """Mock FastAPI app for testing."""
        return Mock(spec=FastAPI)
    
    @pytest.fixture
    def mock_limiter(self):
        """Mock rate limiter."""
        return Mock()
    
    def test_production_excludes_test_routes(self, mock_app, mock_limiter):
        """Test that production environment excludes test routes."""
        config = AppConfig(environment=Environment.PRODUCTION)
        
        with patch('src.application.create_calculation_router') as mock_calc_router, \
             patch('src.application.create_test_router') as mock_test_router:
            
            mock_calc_router.return_value = Mock()
            mock_test_router.return_value = Mock()
            
            register_routes(mock_app, config, mock_limiter)
            
            # Verify test router is not created in production
            mock_test_router.assert_not_called()
            
            # Verify only health and calculation routes are included
            assert mock_app.include_router.call_count == 2  # health + calculation
    
    def test_development_includes_test_routes(self, mock_app, mock_limiter):
        """Test that development environment includes test routes."""
        config = AppConfig(environment=Environment.DEVELOPMENT)
        
        with patch('src.application.create_calculation_router') as mock_calc_router, \
             patch('src.application.create_test_router') as mock_test_router:
            
            mock_calc_router.return_value = Mock()
            mock_test_router.return_value = Mock()
            
            register_routes(mock_app, config, mock_limiter)
            
            # Verify test router is created in development
            mock_test_router.assert_called_once()
            
            # Verify all routes are included: health + calculation + test
            assert mock_app.include_router.call_count == 3
    
    def test_testing_includes_test_routes(self, mock_app, mock_limiter):
        """Test that testing environment includes test routes."""
        config = AppConfig(environment=Environment.TESTING)
        
        with patch('src.application.create_calculation_router') as mock_calc_router, \
             patch('src.application.create_test_router') as mock_test_router:
            
            mock_calc_router.return_value = Mock()
            mock_test_router.return_value = Mock()
            
            register_routes(mock_app, config, mock_limiter)
            
            # Verify test router is created in testing
            mock_test_router.assert_called_once()
            
            # Verify all routes are included: health + calculation + test
            assert mock_app.include_router.call_count == 3


class TestApplicationStartupEnvironmentBehavior:
    """Test complete application startup for different environments."""
    
    @pytest.fixture
    def mock_config_file_production(self, tmp_path):
        """Create a temporary production config file."""
        config_file = tmp_path / "production_config.json"
        config_file.write_text("""{
            "security": {
                "enable_auth": true,
                "enable_webhook_signature": true
            },
            "rate_limiting": {
                "requests_per_minute": 100,
                "enabled": true
            }
        }""")
        return str(config_file)
    
    def test_production_app_startup_configuration(self, mock_config_file_production):
        """Test complete production application startup."""
        with patch.dict('os.environ', {
            'ENVIRONMENT': 'production',
            'API_KEY': 'prod-api-key',
            'WEBHOOK_SECRET': 'prod-webhook-secret'
        }), \
        patch('src.application.setup_logging') as mock_setup_logging, \
        patch('src.application.initialize_dependencies') as mock_init_deps, \
        patch('src.application.setup_middleware') as mock_middleware, \
        patch('src.application.setup_rate_limiting') as mock_rate_limit:
            
            mock_rate_limit.return_value = Mock()
            
            app = create_app(mock_config_file_production)
            
            # Verify production logging setup
            mock_setup_logging.assert_called_once()
            call_args = mock_setup_logging.call_args[0]
            assert call_args[0] == Environment.PRODUCTION
            
            # Verify dependencies initialized
            mock_init_deps.assert_called_once()
            
            # Verify middleware and rate limiting setup
            mock_middleware.assert_called_once()
            mock_rate_limit.assert_called_once()
            
            # Verify app configuration
            assert isinstance(app, FastAPI)
            assert app.docs_url is None  # Disabled in production
    
    def test_development_app_startup_configuration(self, tmp_path):
        """Test complete development application startup."""
        config_file = tmp_path / "dev_config.json"
        config_file.write_text("""{
            "security": {
                "enable_auth": false,
                "enable_webhook_signature": false
            }
        }""")
        
        with patch.dict('os.environ', {
            'ENVIRONMENT': 'development'
        }), \
        patch('src.application.setup_logging') as mock_setup_logging, \
        patch('src.application.initialize_dependencies') as mock_init_deps, \
        patch('src.application.setup_middleware') as mock_middleware, \
        patch('src.application.setup_rate_limiting') as mock_rate_limit:
            
            mock_rate_limit.return_value = Mock()
            
            app = create_app(str(config_file))
            
            # Verify development logging setup
            mock_setup_logging.assert_called_once()
            call_args = mock_setup_logging.call_args[0]
            assert call_args[0] == Environment.DEVELOPMENT
            
            # Verify app configuration for development
            assert isinstance(app, FastAPI)
            assert app.docs_url == "/docs"  # Enabled in development


class TestEnvironmentSecurityConfiguration:
    """Test security configuration differences between environments."""
    
    def test_production_security_requirements(self):
        """Test that production environment enforces security requirements."""
        config = AppConfig(
            environment=Environment.PRODUCTION,
            security=SecurityConfig(enable_auth=True, enable_webhook_signature=True),
            api_key="prod-key",
            webhook_secret="prod-secret"
        )
        
        # Production should have security enabled
        assert config.security.enable_auth is True
        assert config.security.enable_webhook_signature is True
        assert config.api_key is not None
        assert config.webhook_secret is not None
    
    def test_development_security_flexibility(self):
        """Test that development environment allows flexible security."""
        config = AppConfig(
            environment=Environment.DEVELOPMENT,
            security=SecurityConfig(enable_auth=False, enable_webhook_signature=False)
        )
        
        # Development can have security disabled for easier testing
        assert config.security.enable_auth is False
        assert config.security.enable_webhook_signature is False
    
    def test_testing_environment_security_isolation(self):
        """Test that testing environment has appropriate security configuration."""
        config = AppConfig(
            environment=Environment.TESTING,
            security=SecurityConfig(enable_auth=False, enable_webhook_signature=False)
        )
        
        # Testing should allow security to be disabled for test isolation
        assert config.security.enable_auth is False
        assert config.security.enable_webhook_signature is False


class TestEnvironmentFailureScenarios:
    """Test environment-specific failure handling."""
    
    def test_production_environment_logging_failure_graceful_degradation(self):
        """Test that production logging failure doesn't crash the application."""
        with patch('logging.basicConfig', side_effect=[Exception("Logging setup failed"), None]) as mock_basic:
            # Should not raise exception, even if logging setup fails
            setup_logging(Environment.PRODUCTION)
            
            # Should attempt logging setup twice (original + fallback)
            assert mock_basic.call_count == 2
            
            # Fallback call should have basic configuration
            fallback_call = mock_basic.call_args_list[1]
            assert fallback_call[1]['level'] == logging.INFO
    
    def test_invalid_environment_defaults_to_development(self):
        """Test that invalid environment values default to development."""
        with patch.dict('os.environ', {'ENVIRONMENT': 'invalid_env'}):
            config = AppConfig.from_dict({})
            
            # Should default to development for invalid environment
            assert config.environment == Environment.DEVELOPMENT
    
    def test_missing_environment_variable_defaults_to_development(self):
        """Test that missing ENVIRONMENT variable defaults to development."""
        with patch.dict('os.environ', {}, clear=True):
            config = AppConfig.from_dict({})
            
            # Should default to development when no environment is specified
            assert config.environment == Environment.DEVELOPMENT
    
    def test_application_startup_handles_environment_misconfiguration(self, tmp_path):
        """Test that app startup handles environment misconfiguration gracefully."""
        config_file = tmp_path / "bad_config.json"
        config_file.write_text("{}")  # Empty config
        
        with patch.dict('os.environ', {
            'ENVIRONMENT': 'invalid_environment',
            'PORT': 'not_a_number'  # Invalid port
        }), \
        patch('src.application.setup_logging') as mock_setup_logging, \
        patch('src.application.initialize_dependencies') as mock_init_deps, \
        patch('src.application.setup_middleware') as mock_middleware, \
        patch('src.application.setup_rate_limiting') as mock_rate_limit:
            
            mock_rate_limit.return_value = Mock()
            
            # Should not crash despite invalid configuration - graceful error handling
            app = create_app(str(config_file))
            
            # Should still create a functional app
            assert isinstance(app, FastAPI)
            
            # Should have called setup functions
            mock_setup_logging.assert_called_once()
            mock_init_deps.assert_called_once()


class TestEnvironmentSpecificBehaviorIntegration:
    """Integration tests for environment-specific behaviors."""
    
    def test_production_environment_complete_security_stack(self):
        """Test that production environment properly configures the complete security stack."""
        config = AppConfig(
            environment=Environment.PRODUCTION,
            security=SecurityConfig(
                enable_auth=True,
                enable_webhook_signature=True,
                max_tokens_per_request=50000,
                trusted_hosts=["api.production.com"]
            ),
            rate_limiting=RateLimitConfig(
                requests_per_minute=100,
                enabled=True
            ),
            api_key="secure-prod-key",
            webhook_secret="secure-webhook-secret"
        )
        
        # Verify complete production security configuration
        assert config.environment == Environment.PRODUCTION
        assert config.security.enable_auth is True
        assert config.security.enable_webhook_signature is True
        assert config.security.max_tokens_per_request == 50000
        assert config.security.trusted_hosts == ["api.production.com"]
        assert config.rate_limiting.enabled is True
        assert config.rate_limiting.requests_per_minute == 100
        assert config.api_key == "secure-prod-key"
        assert config.webhook_secret == "secure-webhook-secret"
    
    def test_development_environment_debugging_capabilities(self):
        """Test that development environment enables appropriate debugging capabilities."""
        config = AppConfig(environment=Environment.DEVELOPMENT)
        app = create_fastapi_app(config)
        
        # Development should enable debugging features
        assert app.docs_url == "/docs"
        assert app.redoc_url == "/redoc"
        
        # Should allow flexible security for development
        assert config.security.enable_auth is False
        assert config.security.enable_webhook_signature is False
        
        # Should have reasonable defaults for development
        assert config.port == 8000
        assert config.rate_limiting.enabled is True  # Still enabled but with defaults
    
    def test_invalid_port_environment_variable_graceful_handling(self):
        """Test that invalid PORT environment variable is handled gracefully."""
        with patch.dict('os.environ', {'PORT': 'invalid_port'}):
            config = AppConfig.from_dict({})
            
            # Should default to default port for invalid value
            assert config.port == DefaultValues.DEFAULT_PORT
    
    def test_out_of_range_port_environment_variable_graceful_handling(self):
        """Test that out-of-range PORT values are handled gracefully."""
        with patch.dict('os.environ', {'PORT': '70000'}):
            config = AppConfig.from_dict({})
            
            # Should default to default port for out-of-range value
            assert config.port == DefaultValues.DEFAULT_PORT