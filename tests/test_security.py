import pytest
import os
import hashlib
import hmac
from unittest.mock import patch, MagicMock
from fastapi import HTTPException, Request
from fastapi.security import HTTPAuthorizationCredentials
import sys
from pathlib import Path

# Add the parent directory to the path so we can import main
sys.path.insert(0, str(Path(__file__).parent.parent))

from main import verify_api_key, verify_webhook_signature, CONFIG


class TestAPIKeyVerification:
    """Test API key verification functionality"""

    def test_verify_api_key_disabled(self):
        """Test API key verification when auth is disabled"""
        with patch.dict(CONFIG, {"security": {"enable_auth": False}}):
            result = verify_api_key(None)
            assert result is True

    def test_verify_api_key_missing_credentials(self):
        """Test API key verification with missing credentials"""
        with patch.dict(CONFIG, {"security": {"enable_auth": True}}):
            with pytest.raises(HTTPException) as exc_info:
                verify_api_key(None)
            
            assert exc_info.value.status_code == 401
            assert "API key required" in exc_info.value.detail

    def test_verify_api_key_missing_env_var(self):
        """Test API key verification when API_KEY env var is missing"""
        with patch.dict(CONFIG, {"security": {"enable_auth": True}}):
            with patch.dict(os.environ, {}, clear=True):
                credentials = HTTPAuthorizationCredentials(
                    scheme="Bearer",
                    credentials="some-key"
                )
                
                with pytest.raises(HTTPException) as exc_info:
                    verify_api_key(credentials)
                
                assert exc_info.value.status_code == 500
                assert "API key not configured" in exc_info.value.detail

    def test_verify_api_key_invalid(self, env_vars):
        """Test API key verification with invalid key"""
        with patch.dict(CONFIG, {"security": {"enable_auth": True}}):
            credentials = HTTPAuthorizationCredentials(
                scheme="Bearer",
                credentials="wrong-api-key"
            )
            
            with pytest.raises(HTTPException) as exc_info:
                verify_api_key(credentials)
            
            assert exc_info.value.status_code == 401
            assert "Invalid API key" in exc_info.value.detail

    def test_verify_api_key_valid(self, env_vars):
        """Test API key verification with valid key"""
        with patch.dict(CONFIG, {"security": {"enable_auth": True}}):
            credentials = HTTPAuthorizationCredentials(
                scheme="Bearer",
                credentials="test-api-key-12345"
            )
            
            result = verify_api_key(credentials)
            assert result is True

    def test_verify_api_key_timing_attack_protection(self, env_vars):
        """Test that API key comparison uses timing-safe comparison"""
        with patch.dict(CONFIG, {"security": {"enable_auth": True}}):
            with patch('main.hmac.compare_digest') as mock_compare:
                mock_compare.return_value = False
                
                credentials = HTTPAuthorizationCredentials(
                    scheme="Bearer",
                    credentials="test-key"
                )
                
                with pytest.raises(HTTPException):
                    verify_api_key(credentials)
                
                # Verify that hmac.compare_digest was called
                mock_compare.assert_called_once()


class TestWebhookSignatureVerification:
    """Test webhook signature verification functionality"""

    def test_verify_webhook_signature_disabled(self):
        """Test webhook signature verification when disabled"""
        with patch.dict(CONFIG, {"security": {"enable_webhook_signature": False}}):
            mock_request = MagicMock()
            result = verify_webhook_signature(mock_request, b"test body")
            assert result is True

    def test_verify_webhook_signature_missing_header(self):
        """Test webhook signature verification with missing header"""
        with patch.dict(CONFIG, {"security": {"enable_webhook_signature": True}}):
            mock_request = MagicMock()
            mock_request.headers.get.return_value = None
            
            with pytest.raises(HTTPException) as exc_info:
                verify_webhook_signature(mock_request, b"test body")
            
            assert exc_info.value.status_code == 401
            assert "Webhook signature required" in exc_info.value.detail

    def test_verify_webhook_signature_missing_secret(self):
        """Test webhook signature verification when secret is missing"""
        with patch.dict(CONFIG, {"security": {"enable_webhook_signature": True}}):
            with patch.dict(os.environ, {}, clear=True):
                mock_request = MagicMock()
                mock_request.headers.get.return_value = "sha256=somehash"
                
                with pytest.raises(HTTPException) as exc_info:
                    verify_webhook_signature(mock_request, b"test body")
                
                assert exc_info.value.status_code == 500
                assert "Webhook secret not configured" in exc_info.value.detail

    def test_verify_webhook_signature_invalid(self, env_vars):
        """Test webhook signature verification with invalid signature"""
        with patch.dict(CONFIG, {"security": {"enable_webhook_signature": True}}):
            mock_request = MagicMock()
            mock_request.headers.get.return_value = "sha256=invalid_hash"
            
            with pytest.raises(HTTPException) as exc_info:
                verify_webhook_signature(mock_request, b"test body")
            
            assert exc_info.value.status_code == 401
            assert "Invalid webhook signature" in exc_info.value.detail

    def test_verify_webhook_signature_valid(self, env_vars):
        """Test webhook signature verification with valid signature"""
        with patch.dict(CONFIG, {"security": {"enable_webhook_signature": True}}):
            body = b"test request body"
            webhook_secret = "test-webhook-secret-67890"
            
            # Generate valid signature
            expected_signature = hmac.new(
                webhook_secret.encode(),
                body,
                hashlib.sha256
            ).hexdigest()
            signature_header = f"sha256={expected_signature}"
            
            mock_request = MagicMock()
            mock_request.headers.get.return_value = signature_header
            
            result = verify_webhook_signature(mock_request, body)
            assert result is True

    def test_verify_webhook_signature_timing_attack_protection(self, env_vars):
        """Test that signature comparison uses timing-safe comparison"""
        with patch.dict(CONFIG, {"security": {"enable_webhook_signature": True}}):
            with patch('main.hmac.compare_digest') as mock_compare:
                mock_compare.return_value = False
                
                mock_request = MagicMock()
                mock_request.headers.get.return_value = "sha256=test_signature"
                
                with pytest.raises(HTTPException):
                    verify_webhook_signature(mock_request, b"test body")
                
                # Verify that hmac.compare_digest was called
                mock_compare.assert_called_once()

    def test_verify_webhook_signature_different_body_content(self, env_vars):
        """Test webhook signature with different body content"""
        with patch.dict(CONFIG, {"security": {"enable_webhook_signature": True}}):
            webhook_secret = "test-webhook-secret-67890"
            original_body = b"original body"
            different_body = b"different body"
            
            # Generate signature for original body
            signature = hmac.new(
                webhook_secret.encode(),
                original_body,
                hashlib.sha256
            ).hexdigest()
            signature_header = f"sha256={signature}"
            
            mock_request = MagicMock()
            mock_request.headers.get.return_value = signature_header
            
            # Verify with different body should fail
            with pytest.raises(HTTPException) as exc_info:
                verify_webhook_signature(mock_request, different_body)
            
            assert exc_info.value.status_code == 401
            assert "Invalid webhook signature" in exc_info.value.detail

    def test_verify_webhook_signature_malformed_header(self, env_vars):
        """Test webhook signature with malformed signature header"""
        with patch.dict(CONFIG, {"security": {"enable_webhook_signature": True}}):
            mock_request = MagicMock()
            mock_request.headers.get.return_value = "invalid_format_signature"
            
            with pytest.raises(HTTPException) as exc_info:
                verify_webhook_signature(mock_request, b"test body")
            
            assert exc_info.value.status_code == 401
            assert "Invalid webhook signature" in exc_info.value.detail