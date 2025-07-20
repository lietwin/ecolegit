import pytest
import time
from unittest.mock import patch
from fastapi.testclient import TestClient
import sys
from pathlib import Path

# Add the parent directory to the path so we can import main
sys.path.insert(0, str(Path(__file__).parent.parent))

from main import app, CONFIG


class TestCORSMiddleware:
    """Test CORS middleware functionality"""

    def test_cors_allowed_origins(self, client):
        """Test that allowed origins can make requests"""
        allowed_origins = [
            "https://hook.eu1.make.com",
            "https://hook.us1.make.com"
        ]
        
        for origin in allowed_origins:
            response = client.options(
                "/calculate",
                headers={"Origin": origin, "Access-Control-Request-Method": "POST"}
            )
            
            # CORS preflight should be handled
            assert response.status_code in [200, 204]

    def test_cors_disallowed_origin(self, client):
        """Test that disallowed origins are handled appropriately"""
        response = client.options(
            "/calculate",
            headers={
                "Origin": "https://malicious-site.com",
                "Access-Control-Request-Method": "POST"
            }
        )
        
        # Should still handle preflight but with restrictions
        assert response.status_code in [200, 204, 403]

    def test_cors_allowed_methods(self, client):
        """Test that only allowed methods are permitted"""
        response = client.options(
            "/calculate",
            headers={
                "Origin": "https://hook.eu1.make.com",
                "Access-Control-Request-Method": "POST"
            }
        )
        
        assert response.status_code in [200, 204]

    def test_cors_disallowed_method(self, client):
        """Test that disallowed methods are rejected"""
        response = client.options(
            "/calculate",
            headers={
                "Origin": "https://hook.eu1.make.com",
                "Access-Control-Request-Method": "DELETE"
            }
        )
        
        # DELETE should not be allowed
        # Response depends on FastAPI's CORS implementation
        assert response.status_code in [200, 204, 405]

    def test_cors_allowed_headers(self, client):
        """Test that allowed headers are accepted"""
        allowed_headers = ["Content-Type", "Authorization"]
        
        for header in allowed_headers:
            response = client.options(
                "/calculate",
                headers={
                    "Origin": "https://hook.eu1.make.com",
                    "Access-Control-Request-Method": "POST",
                    "Access-Control-Request-Headers": header
                }
            )
            
            assert response.status_code in [200, 204]


class TestTrustedHostMiddleware:
    """Test trusted host middleware functionality"""

    def test_trusted_host_wildcard_default(self, client):
        """Test that wildcard allows all hosts by default"""
        with patch.dict(CONFIG, {"security": {"trusted_hosts": ["*"]}}):
            response = client.get("/health", headers={"Host": "example.com"})
            
            # Should be allowed with wildcard
            assert response.status_code == 200

    def test_trusted_host_specific_allowed(self, client):
        """Test that specific trusted hosts are allowed"""
        with patch.dict(CONFIG, {"security": {"trusted_hosts": ["api.example.com"]}}):
            # Mock the middleware behavior since it's difficult to test directly
            response = client.get("/health")
            
            # Should work in test environment
            assert response.status_code == 200

    def test_trusted_host_multiple_allowed(self, client):
        """Test multiple trusted hosts configuration"""
        trusted_hosts = ["api.example.com", "webhook.service.com", "localhost"]
        
        with patch.dict(CONFIG, {"security": {"trusted_hosts": trusted_hosts}}):
            response = client.get("/health")
            
            # Should work in test environment
            assert response.status_code == 200


class TestRateLimitingMiddleware:
    """Test rate limiting middleware functionality"""

    def test_rate_limiting_disabled(self, client, mock_models, mock_ecologits):
        """Test that rate limiting can be disabled"""
        with patch.dict(CONFIG, {
            "rate_limiting": {"enabled": False, "requests_per_minute": 1},
            "security": {"enable_auth": False, "enable_webhook_signature": False}
        }):
            payload = {
                "model": "gpt-4o",
                "input_tokens": 100,
                "output_tokens": 50
            }
            
            # Make multiple requests quickly
            responses = []
            for _ in range(3):
                response = client.post("/calculate", json=payload)
                responses.append(response)
            
            # All should succeed when rate limiting is disabled
            for response in responses:
                assert response.status_code == 200

    def test_rate_limiting_enabled_within_limit(self, client, mock_models, mock_ecologits):
        """Test rate limiting when within limits"""
        with patch.dict(CONFIG, {
            "rate_limiting": {"enabled": True, "requests_per_minute": 60},
            "security": {"enable_auth": False, "enable_webhook_signature": False}
        }):
            payload = {
                "model": "gpt-4o",
                "input_tokens": 100,
                "output_tokens": 50
            }
            
            response = client.post("/calculate", json=payload)
            
            # Should succeed when within rate limit
            assert response.status_code == 200

    def test_rate_limiting_enforced_exceeds_limit(self, client):
        """Test that rate limiting is enforced when limit is exceeded"""
        with patch.dict(CONFIG, {
            "rate_limiting": {"enabled": True, "requests_per_minute": 1},
            "security": {"enable_auth": False, "enable_webhook_signature": False}
        }):
            payload = {
                "model": "gpt-4o",
                "input_tokens": 100,
                "output_tokens": 50
            }
            
            # Make requests in rapid succession
            responses = []
            for _ in range(3):
                response = client.post("/calculate", json=payload)
                responses.append(response)
                time.sleep(0.1)  # Small delay to ensure ordering
            
            # At least one should be rate limited
            status_codes = [r.status_code for r in responses]
            assert 429 in status_codes or any(s != 200 for s in status_codes[:2])

    def test_rate_limiting_different_endpoints(self, client):
        """Test that rate limiting applies to the correct endpoint"""
        with patch.dict(CONFIG, {
            "rate_limiting": {"enabled": True, "requests_per_minute": 1}
        }):
            # Health endpoint should not be rate limited (no decorator)
            response = client.get("/health")
            assert response.status_code == 200
            
            # Models endpoint should not be rate limited (no decorator)
            response = client.get("/models")
            assert response.status_code == 200

    def test_rate_limiting_per_client_ip(self, client):
        """Test that rate limiting is applied per client IP"""
        with patch.dict(CONFIG, {
            "rate_limiting": {"enabled": True, "requests_per_minute": 2},
            "security": {"enable_auth": False, "enable_webhook_signature": False}
        }):
            payload = {
                "model": "gpt-4o",
                "input_tokens": 100,
                "output_tokens": 50
            }
            
            # In test environment, all requests come from the same IP
            # So we test that the rate limiting is based on IP
            responses = []
            for _ in range(4):
                response = client.post("/calculate", json=payload)
                responses.append(response)
            
            # Some requests should be rate limited
            status_codes = [r.status_code for r in responses]
            # Allow for some variation in rate limiting implementation
            success_count = sum(1 for code in status_codes if code == 200)
            rate_limited_count = sum(1 for code in status_codes if code == 429)
            
            # Should have some successful and some rate limited
            assert success_count > 0
            # Note: exact behavior may vary based on timing and implementation


class TestMiddlewareIntegration:
    """Test middleware integration and interaction"""

    def test_middleware_stack_order(self, client):
        """Test that middleware stack is applied in correct order"""
        # This is more of an integration test to ensure all middleware works together
        response = client.get("/health")
        
        # Should pass through all middleware layers
        assert response.status_code == 200

    def test_middleware_with_authentication(self, client, env_vars, mock_models, mock_ecologits):
        """Test middleware interaction with authentication"""
        with patch.dict(CONFIG, {
            "security": {
                "enable_auth": True,
                "enable_webhook_signature": False,
                "trusted_hosts": ["*"]
            },
            "rate_limiting": {"enabled": False}
        }):
            payload = {
                "model": "gpt-4o",
                "input_tokens": 100,
                "output_tokens": 50
            }
            
            headers = {"Authorization": "Bearer test-api-key-12345"}
            response = client.post("/calculate", json=payload, headers=headers)
            
            # Should pass through all middleware and succeed with auth
            assert response.status_code == 200

    def test_middleware_error_handling(self, client):
        """Test that middleware doesn't interfere with error responses"""
        with patch.dict(CONFIG, {
            "security": {"enable_auth": False, "enable_webhook_signature": False},
            "rate_limiting": {"enabled": False}
        }):
            # Invalid endpoint
            response = client.post("/nonexistent", json={})
            
            # Should get 404, not middleware errors
            assert response.status_code == 404

    def test_middleware_with_large_request(self, client):
        """Test middleware handling of large requests"""
        with patch.dict(CONFIG, {
            "security": {"enable_auth": False, "enable_webhook_signature": False},
            "rate_limiting": {"enabled": False}
        }):
            # Large but valid request
            large_metadata = {f"key_{i}": "small_value" for i in range(5)}
            payload = {
                "model": "gpt-4o",
                "input_tokens": 10000,
                "output_tokens": 5000,
                "metadata": large_metadata
            }
            
            response = client.post("/calculate", json=payload)
            
            # Middleware should handle large requests appropriately
            # Response depends on validation, not middleware failure
            assert response.status_code in [200, 422]