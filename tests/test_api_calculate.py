import pytest
import json
import hashlib
import hmac
import time
from unittest.mock import patch, MagicMock
from fastapi.testclient import TestClient
import sys
from pathlib import Path

# Add the parent directory to the path so we can import main
sys.path.insert(0, str(Path(__file__).parent.parent))

from main import app, CONFIG


class TestCalculateEndpoint:
    """Test the main /calculate endpoint functionality"""

    def test_calculate_endpoint_success(self, client, mock_models, mock_ecologits, env_vars):
        """Test successful calculation request"""
        with patch.dict(CONFIG, {
            "security": {"enable_auth": False, "enable_webhook_signature": False},
            "rate_limiting": {"enabled": False}
        }):
            payload = {
                "model": "gpt-4o",
                "input_tokens": 1000,
                "output_tokens": 500,
                "metadata": {"user_id": "test123"}
            }
            
            response = client.post("/calculate", json=payload)
            
            assert response.status_code == 200
            data = response.json()
            
            assert data["model"] == "gpt-4o"
            assert data["input_tokens"] == 1000
            assert data["output_tokens"] == 500
            assert data["total_tokens"] == 1500
            assert data["energy_kwh"] == 0.001234
            assert data["gwp_kgco2eq"] == 0.000567
            assert data["success"] is True
            assert data["error"] is None
            assert data["calculation_id"].startswith("calc-")
            assert "timestamp" in data

    def test_calculate_endpoint_invalid_model_name(self, client):
        """Test request with invalid model name characters"""
        with patch.dict(CONFIG, {
            "security": {"enable_auth": False, "enable_webhook_signature": False},
            "rate_limiting": {"enabled": False}
        }):
            payload = {
                "model": "gpt-4o@invalid!",
                "input_tokens": 1000,
                "output_tokens": 500
            }
            
            response = client.post("/calculate", json=payload)
            
            assert response.status_code == 422
            assert "Model name contains invalid characters" in response.text

    def test_calculate_endpoint_negative_tokens(self, client):
        """Test request with negative token counts"""
        with patch.dict(CONFIG, {
            "security": {"enable_auth": False, "enable_webhook_signature": False},
            "rate_limiting": {"enabled": False}
        }):
            payload = {
                "model": "gpt-4o",
                "input_tokens": -100,
                "output_tokens": 500
            }
            
            response = client.post("/calculate", json=payload)
            
            assert response.status_code == 422

    def test_calculate_endpoint_excessive_tokens(self, client):
        """Test request with token count exceeding limits"""
        with patch.dict(CONFIG, {
            "security": {"enable_auth": False, "enable_webhook_signature": False, "max_tokens_per_request": 1000},
            "rate_limiting": {"enabled": False}
        }):
            payload = {
                "model": "gpt-4o",
                "input_tokens": 1001,  # Exceeds limit
                "output_tokens": 500
            }
            
            response = client.post("/calculate", json=payload)
            
            assert response.status_code == 422

    def test_calculate_endpoint_rate_limit(self, client):
        """Test rate limiting behavior"""
        with patch.dict(CONFIG, {
            "security": {"enable_auth": False, "enable_webhook_signature": False},
            "rate_limiting": {"enabled": True, "requests_per_minute": 1}
        }):
            payload = {
                "model": "gpt-4o",
                "input_tokens": 100,
                "output_tokens": 50
            }
            
            # First request should succeed
            response1 = client.post("/calculate", json=payload)
            
            # Second immediate request should be rate limited
            response2 = client.post("/calculate", json=payload)
            
            # One should succeed, one should be rate limited
            status_codes = {response1.status_code, response2.status_code}
            assert 200 in status_codes
            assert 429 in status_codes

    def test_calculate_endpoint_auth_required_missing_key(self, client, env_vars):
        """Test authentication when API key is required but missing"""
        with patch.dict(CONFIG, {
            "security": {"enable_auth": True, "enable_webhook_signature": False},
            "rate_limiting": {"enabled": False}
        }):
            payload = {
                "model": "gpt-4o",
                "input_tokens": 1000,
                "output_tokens": 500
            }
            
            response = client.post("/calculate", json=payload)
            
            assert response.status_code == 401
            assert "API key required" in response.json()["detail"]

    def test_calculate_endpoint_auth_required_valid_key(self, client, env_vars, mock_models, mock_ecologits):
        """Test authentication with valid API key"""
        with patch.dict(CONFIG, {
            "security": {"enable_auth": True, "enable_webhook_signature": False},
            "rate_limiting": {"enabled": False}
        }):
            payload = {
                "model": "gpt-4o",
                "input_tokens": 1000,
                "output_tokens": 500
            }
            
            headers = {"Authorization": "Bearer test-api-key-12345"}
            response = client.post("/calculate", json=payload, headers=headers)
            
            assert response.status_code == 200

    def test_calculate_endpoint_auth_required_invalid_key(self, client, env_vars):
        """Test authentication with invalid API key"""
        with patch.dict(CONFIG, {
            "security": {"enable_auth": True, "enable_webhook_signature": False},
            "rate_limiting": {"enabled": False}
        }):
            payload = {
                "model": "gpt-4o",
                "input_tokens": 1000,
                "output_tokens": 500
            }
            
            headers = {"Authorization": "Bearer wrong-api-key"}
            response = client.post("/calculate", json=payload, headers=headers)
            
            assert response.status_code == 401
            assert "Invalid API key" in response.json()["detail"]

    def test_calculate_endpoint_webhook_signature_required(self, client, env_vars, mock_models, mock_ecologits):
        """Test webhook signature verification"""
        with patch.dict(CONFIG, {
            "security": {"enable_auth": False, "enable_webhook_signature": True},
            "rate_limiting": {"enabled": False}
        }):
            payload = {
                "model": "gpt-4o",
                "input_tokens": 1000,
                "output_tokens": 500
            }
            
            body = json.dumps(payload).encode()
            webhook_secret = "test-webhook-secret-67890"
            
            # Generate valid signature
            signature = hmac.new(
                webhook_secret.encode(),
                body,
                hashlib.sha256
            ).hexdigest()
            
            headers = {"X-Webhook-Signature": f"sha256={signature}"}
            response = client.post("/calculate", json=payload, headers=headers)
            
            assert response.status_code == 200

    def test_calculate_endpoint_webhook_signature_invalid(self, client, env_vars):
        """Test webhook signature verification with invalid signature"""
        with patch.dict(CONFIG, {
            "security": {"enable_auth": False, "enable_webhook_signature": True},
            "rate_limiting": {"enabled": False}
        }):
            payload = {
                "model": "gpt-4o",
                "input_tokens": 1000,
                "output_tokens": 500
            }
            
            headers = {"X-Webhook-Signature": "sha256=invalid_signature"}
            response = client.post("/calculate", json=payload, headers=headers)
            
            assert response.status_code == 401
            assert "Invalid webhook signature" in response.json()["detail"]

    def test_calculate_endpoint_malformed_json(self, client):
        """Test request with malformed JSON"""
        with patch.dict(CONFIG, {
            "security": {"enable_auth": False, "enable_webhook_signature": False},
            "rate_limiting": {"enabled": False}
        }):
            response = client.post(
                "/calculate",
                data='{"model": "gpt-4o", "input_tokens": invalid}',  # Invalid JSON
                headers={"Content-Type": "application/json"}
            )
            
            assert response.status_code == 422

    def test_calculate_endpoint_missing_required_fields(self, client):
        """Test request with missing required fields"""
        with patch.dict(CONFIG, {
            "security": {"enable_auth": False, "enable_webhook_signature": False},
            "rate_limiting": {"enabled": False}
        }):
            # Missing output_tokens
            payload = {
                "model": "gpt-4o",
                "input_tokens": 1000
            }
            
            response = client.post("/calculate", json=payload)
            
            assert response.status_code == 422

    def test_calculate_endpoint_calculation_id_unique(self, client, mock_models, mock_ecologits):
        """Test that calculation IDs are unique across requests"""
        with patch.dict(CONFIG, {
            "security": {"enable_auth": False, "enable_webhook_signature": False},
            "rate_limiting": {"enabled": False}
        }):
            payload = {
                "model": "gpt-4o",
                "input_tokens": 1000,
                "output_tokens": 500
            }
            
            response1 = client.post("/calculate", json=payload)
            response2 = client.post("/calculate", json=payload)
            
            assert response1.status_code == 200
            assert response2.status_code == 200
            
            data1 = response1.json()
            data2 = response2.json()
            
            assert data1["calculation_id"] != data2["calculation_id"]

    def test_calculate_endpoint_unsupported_model(self, client):
        """Test calculation with unsupported model"""
        with patch.dict(CONFIG, {
            "security": {"enable_auth": False, "enable_webhook_signature": False},
            "rate_limiting": {"enabled": False}
        }):
            with patch('main.models', {}):  # Empty models dict
                payload = {
                    "model": "unknown-model",
                    "input_tokens": 1000,
                    "output_tokens": 500
                }
                
                response = client.post("/calculate", json=payload)
                
                assert response.status_code == 200
                data = response.json()
                
                assert data["success"] is False
                assert "not supported" in data["error"]
                assert data["energy_kwh"] == 0.0
                assert data["gwp_kgco2eq"] == 0.0

    def test_calculate_endpoint_large_metadata(self, client):
        """Test request with metadata exceeding size limit"""
        with patch.dict(CONFIG, {
            "security": {"enable_auth": False, "enable_webhook_signature": False},
            "rate_limiting": {"enabled": False}
        }):
            # Create large metadata that exceeds 1KB
            large_metadata = {f"key_{i}": "x" * 100 for i in range(20)}
            
            payload = {
                "model": "gpt-4o",
                "input_tokens": 1000,
                "output_tokens": 500,
                "metadata": large_metadata
            }
            
            response = client.post("/calculate", json=payload)
            
            assert response.status_code == 422
            assert "Metadata too large" in response.text

    def test_calculate_endpoint_timestamp_format(self, client, mock_models, mock_ecologits):
        """Test that timestamp is in correct ISO format"""
        with patch.dict(CONFIG, {
            "security": {"enable_auth": False, "enable_webhook_signature": False},
            "rate_limiting": {"enabled": False}
        }):
            payload = {
                "model": "gpt-4o",
                "input_tokens": 1000,
                "output_tokens": 500
            }
            
            response = client.post("/calculate", json=payload)
            
            assert response.status_code == 200
            data = response.json()
            
            # Check timestamp format (ISO 8601)
            timestamp = data["timestamp"]
            assert "T" in timestamp
            assert timestamp.endswith("Z") or "+" in timestamp or timestamp.count(":") >= 2

    def test_calculate_endpoint_calculation_error(self, client, mock_models):
        """Test handling of calculation errors"""
        with patch.dict(CONFIG, {
            "security": {"enable_auth": False, "enable_webhook_signature": False},
            "rate_limiting": {"enabled": False}
        }):
            with patch('main.Impacts') as mock_impacts_class:
                mock_impacts_class.from_model_and_tokens.side_effect = Exception("Calculation failed")
                
                payload = {
                    "model": "gpt-4o",
                    "input_tokens": 1000,
                    "output_tokens": 500
                }
                
                response = client.post("/calculate", json=payload)
                
                assert response.status_code == 200
                data = response.json()
                
                assert data["success"] is False
                assert data["error"] == "Internal calculation error"
                assert data["energy_kwh"] == 0.0
                assert data["gwp_kgco2eq"] == 0.0