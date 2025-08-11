"""Comprehensive tests for security module - CRITICAL for production."""

import pytest
import hmac
import hashlib
from unittest.mock import Mock, patch
from fastapi import HTTPException, Request
from fastapi.security import HTTPAuthorizationCredentials

from src.infrastructure.security import (
    SecurityError,
    verify_api_key,
    verify_webhook_signature,
    SecurityManager,
    create_security_manager
)
from src.config.settings import AppConfig, SecurityConfig
from src.config.constants import HTTPStatus, ErrorMessages


class TestSecurityError:
    """Test SecurityError exception."""
    
    def test_security_error_creation(self):
        """Test SecurityError can be created and raised."""
        error = SecurityError("Test security error")
        assert str(error) == "Test security error"
        assert isinstance(error, Exception)


class TestVerifyApiKey:
    """Test API key verification function - CRITICAL for authentication."""
    
    @pytest.fixture
    def config_auth_disabled(self):
        """Config with authentication disabled."""
        return AppConfig(
            security=SecurityConfig(enable_auth=False),
            api_key="test-key"
        )
    
    @pytest.fixture
    def config_auth_enabled(self):
        """Config with authentication enabled."""
        return AppConfig(
            security=SecurityConfig(enable_auth=True),
            api_key="test-secret-key-123"
        )
    
    @pytest.fixture
    def config_auth_enabled_no_key(self):
        """Config with authentication enabled but no API key configured."""
        return AppConfig(
            security=SecurityConfig(enable_auth=True),
            api_key=None
        )
    
    def test_auth_disabled_returns_true(self, config_auth_disabled):
        """Test that when auth is disabled, always returns True."""
        result = verify_api_key(config_auth_disabled, None)
        assert result is True
        
        # Even with credentials, should return True when auth disabled
        credentials = HTTPAuthorizationCredentials(scheme="Bearer", credentials="anything")
        result = verify_api_key(config_auth_disabled, credentials)
        assert result is True
    
    def test_auth_enabled_no_credentials_raises_401(self, config_auth_enabled):
        """Test that missing credentials raises 401 when auth is enabled."""
        with pytest.raises(HTTPException) as exc_info:
            verify_api_key(config_auth_enabled, None)
        
        assert exc_info.value.status_code == HTTPStatus.UNAUTHORIZED
        assert exc_info.value.detail == ErrorMessages.API_KEY_REQUIRED
    
    def test_auth_enabled_no_api_key_configured_raises_500(self, config_auth_enabled_no_key):
        """Test that missing API key config raises 500 - critical misconfiguration."""
        credentials = HTTPAuthorizationCredentials(scheme="Bearer", credentials="any-key")
        
        with pytest.raises(HTTPException) as exc_info:
            verify_api_key(config_auth_enabled_no_key, credentials)
        
        assert exc_info.value.status_code == HTTPStatus.INTERNAL_SERVER_ERROR
        assert exc_info.value.detail == ErrorMessages.API_KEY_NOT_CONFIGURED
    
    def test_auth_enabled_invalid_key_raises_401(self, config_auth_enabled):
        """Test that invalid API key raises 401."""
        credentials = HTTPAuthorizationCredentials(scheme="Bearer", credentials="wrong-key")
        
        with pytest.raises(HTTPException) as exc_info:
            verify_api_key(config_auth_enabled, credentials)
        
        assert exc_info.value.status_code == HTTPStatus.UNAUTHORIZED
        assert exc_info.value.detail == ErrorMessages.INVALID_API_KEY
    
    def test_auth_enabled_valid_key_returns_true(self, config_auth_enabled):
        """Test that valid API key returns True."""
        credentials = HTTPAuthorizationCredentials(
            scheme="Bearer", 
            credentials="test-secret-key-123"
        )
        
        result = verify_api_key(config_auth_enabled, credentials)
        assert result is True
    
    def test_timing_attack_protection(self, config_auth_enabled):
        """Test that hmac.compare_digest is used for timing attack protection."""
        with patch('hmac.compare_digest') as mock_compare:
            mock_compare.return_value = True
            
            credentials = HTTPAuthorizationCredentials(
                scheme="Bearer",
                credentials="test-key"
            )
            
            verify_api_key(config_auth_enabled, credentials)
            
            # Verify hmac.compare_digest was called
            mock_compare.assert_called_once_with("test-key", "test-secret-key-123")


class TestVerifyWebhookSignature:
    """Test webhook signature verification - CRITICAL for webhook security."""
    
    @pytest.fixture
    def config_webhook_disabled(self):
        """Config with webhook signature verification disabled."""
        return AppConfig(
            security=SecurityConfig(enable_webhook_signature=False),
            webhook_secret="test-secret"
        )
    
    @pytest.fixture
    def config_webhook_enabled(self):
        """Config with webhook signature verification enabled."""
        return AppConfig(
            security=SecurityConfig(enable_webhook_signature=True),
            webhook_secret="webhook-secret-key"
        )
    
    @pytest.fixture
    def config_webhook_enabled_no_secret(self):
        """Config with webhook verification enabled but no secret configured."""
        return AppConfig(
            security=SecurityConfig(enable_webhook_signature=True),
            webhook_secret=None
        )
    
    @pytest.fixture
    def mock_request_with_signature(self):
        """Mock request with webhook signature header."""
        request = Mock(spec=Request)
        request.headers.get.return_value = "sha256=test-signature"
        return request
    
    @pytest.fixture
    def mock_request_no_signature(self):
        """Mock request without webhook signature header."""
        request = Mock(spec=Request)
        request.headers.get.return_value = None
        return request
    
    def test_webhook_disabled_returns_true(self, config_webhook_disabled, mock_request_no_signature):
        """Test that when webhook verification is disabled, always returns True."""
        result = verify_webhook_signature(config_webhook_disabled, mock_request_no_signature, b"body")
        assert result is True
    
    def test_webhook_enabled_no_signature_raises_401(self, config_webhook_enabled, mock_request_no_signature):
        """Test that missing signature header raises 401."""
        with pytest.raises(HTTPException) as exc_info:
            verify_webhook_signature(config_webhook_enabled, mock_request_no_signature, b"body")
        
        assert exc_info.value.status_code == HTTPStatus.UNAUTHORIZED
        assert exc_info.value.detail == ErrorMessages.WEBHOOK_SIGNATURE_REQUIRED
    
    def test_webhook_enabled_no_secret_configured_raises_500(self, config_webhook_enabled_no_secret, mock_request_with_signature):
        """Test that missing webhook secret raises 500 - critical misconfiguration."""
        with pytest.raises(HTTPException) as exc_info:
            verify_webhook_signature(config_webhook_enabled_no_secret, mock_request_with_signature, b"body")
        
        assert exc_info.value.status_code == HTTPStatus.INTERNAL_SERVER_ERROR
        assert exc_info.value.detail == ErrorMessages.WEBHOOK_SECRET_NOT_CONFIGURED
    
    def test_webhook_valid_signature_returns_true(self, config_webhook_enabled):
        """Test that valid webhook signature returns True."""
        # Create valid signature
        body = b"test webhook body"
        expected_signature = hmac.new(
            "webhook-secret-key".encode(),
            body,
            hashlib.sha256
        ).hexdigest()
        signature_header = f"sha256={expected_signature}"
        
        # Mock request with correct signature
        request = Mock(spec=Request)
        request.headers.get.return_value = signature_header
        
        result = verify_webhook_signature(config_webhook_enabled, request, body)
        assert result is True
    
    def test_webhook_invalid_signature_raises_401(self, config_webhook_enabled, mock_request_with_signature):
        """Test that invalid webhook signature raises 401."""
        # mock_request_with_signature has "sha256=test-signature" which will be invalid
        with pytest.raises(HTTPException) as exc_info:
            verify_webhook_signature(config_webhook_enabled, mock_request_with_signature, b"body")
        
        assert exc_info.value.status_code == HTTPStatus.UNAUTHORIZED
        assert exc_info.value.detail == ErrorMessages.INVALID_WEBHOOK_SIGNATURE
    
    def test_webhook_signature_timing_attack_protection(self, config_webhook_enabled):
        """Test that hmac.compare_digest is used for timing attack protection."""
        with patch('hmac.compare_digest') as mock_compare:
            mock_compare.return_value = True
            
            request = Mock(spec=Request)
            request.headers.get.return_value = "sha256=test-sig"
            
            verify_webhook_signature(config_webhook_enabled, request, b"body")
            
            # Verify hmac.compare_digest was called for signature comparison
            mock_compare.assert_called_once()
    
    def test_webhook_signature_algorithm_sha256(self, config_webhook_enabled):
        """Test that SHA256 algorithm is used correctly."""
        body = b"test message"
        secret = "webhook-secret-key"
        
        # Calculate expected signature manually
        expected_signature = hmac.new(secret.encode(), body, hashlib.sha256).hexdigest()
        signature_header = f"sha256={expected_signature}"
        
        request = Mock(spec=Request)
        request.headers.get.return_value = signature_header
        
        result = verify_webhook_signature(config_webhook_enabled, request, body)
        assert result is True


class TestSecurityManager:
    """Test SecurityManager class - wrapper for security functions."""
    
    @pytest.fixture
    def config(self):
        """Basic config for SecurityManager tests."""
        return AppConfig(
            security=SecurityConfig(enable_auth=True, enable_webhook_signature=True),
            api_key="test-key",
            webhook_secret="test-secret"
        )
    
    @pytest.fixture
    def security_manager(self, config):
        """SecurityManager instance for testing."""
        return SecurityManager(config)
    
    def test_security_manager_init(self, config):
        """Test SecurityManager initialization."""
        manager = SecurityManager(config)
        assert manager._config == config
    
    def test_verify_authentication_delegates_to_verify_api_key(self, security_manager):
        """Test that verify_authentication calls verify_api_key."""
        with patch('src.infrastructure.security.verify_api_key') as mock_verify:
            mock_verify.return_value = True
            
            credentials = HTTPAuthorizationCredentials(scheme="Bearer", credentials="test-key")
            result = security_manager.verify_authentication(credentials)
            
            assert result is True
            mock_verify.assert_called_once_with(security_manager._config, credentials)
    
    def test_verify_webhook_signature_delegates_to_verify_webhook_signature(self, security_manager):
        """Test that SecurityManager.verify_webhook_signature delegates correctly."""
        with patch('src.infrastructure.security.verify_webhook_signature') as mock_verify:
            mock_verify.return_value = True
            
            request = Mock(spec=Request)
            body = b"test body"
            
            result = security_manager.verify_webhook_signature(request, body)
            
            assert result is True
            mock_verify.assert_called_once_with(security_manager._config, request, body)


class TestCreateSecurityManager:
    """Test security manager factory function."""
    
    def test_create_security_manager_returns_security_manager(self):
        """Test that create_security_manager returns SecurityManager instance."""
        config = AppConfig()
        
        manager = create_security_manager(config)
        
        assert isinstance(manager, SecurityManager)
        assert manager._config == config


class TestSecurityIntegration:
    """Integration tests for security scenarios."""
    
    def test_full_authentication_flow_success(self):
        """Test complete authentication flow with valid credentials."""
        config = AppConfig(
            security=SecurityConfig(enable_auth=True),
            api_key="production-api-key-123"
        )
        
        credentials = HTTPAuthorizationCredentials(
            scheme="Bearer",
            credentials="production-api-key-123"
        )
        
        # Should not raise any exceptions
        result = verify_api_key(config, credentials)
        assert result is True
    
    def test_full_webhook_verification_flow_success(self):
        """Test complete webhook verification flow with valid signature."""
        config = AppConfig(
            security=SecurityConfig(enable_webhook_signature=True),
            webhook_secret="production-webhook-secret"
        )
        
        # Simulate real webhook payload
        body = b'{"model":"gpt-4o","input_tokens":1000,"output_tokens":500}'
        
        # Create valid signature as a webhook would
        signature = hmac.new(
            "production-webhook-secret".encode(),
            body,
            hashlib.sha256
        ).hexdigest()
        
        request = Mock(spec=Request)
        request.headers.get.return_value = f"sha256={signature}"
        
        # Should not raise any exceptions
        result = verify_webhook_signature(config, request, body)
        assert result is True
    
    def test_security_misconfiguration_detection(self):
        """Test that security misconfigurations are detected early."""
        # Auth enabled but no API key
        config = AppConfig(
            security=SecurityConfig(enable_auth=True),
            api_key=None
        )
        
        credentials = HTTPAuthorizationCredentials(scheme="Bearer", credentials="any-key")
        
        # Should raise 500 indicating server misconfiguration
        with pytest.raises(HTTPException) as exc_info:
            verify_api_key(config, credentials)
        
        assert exc_info.value.status_code == HTTPStatus.INTERNAL_SERVER_ERROR