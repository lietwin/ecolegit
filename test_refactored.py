"""Simple test to verify refactored application works."""

import sys
import os
sys.path.insert(0, os.path.dirname(__file__))

from fastapi.testclient import TestClient
from src.application import create_app

def test_refactored_app():
    """Test that the refactored application starts and basic endpoints work."""
    try:
        # Create app
        app = create_app()
        client = TestClient(app)
        
        # Test health endpoint
        response = client.get("/health")
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "healthy"
        assert data["service"] == "ecologits-webhook"
        print("✅ Health endpoint works")
        
        # Test models endpoint
        response = client.get("/models")
        assert response.status_code == 200
        data = response.json()
        assert "supported_models" in data
        assert "total_ecologits_models" in data
        print("✅ Models endpoint works")
        
        # Test docs are available (development mode)
        response = client.get("/docs")
        assert response.status_code == 200
        print("✅ Docs endpoint works")
        
        print("🎉 All basic tests passed!")
        return True
        
    except Exception as e:
        print(f"❌ Test failed: {e}")
        return False

if __name__ == "__main__":
    test_refactored_app()