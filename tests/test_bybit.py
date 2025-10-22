"""
Tests for ByBit exchange endpoints.

All tests use mocks to avoid real API calls and trading operations.
Tests focus on authentication and error conditions rather than mocking internal logic.
"""
from fastapi.testclient import TestClient
from api_main import app


client = TestClient(app)


def get_auth_token():
    """Helper function to get authentication token."""
    response = client.post(
        "/token",
        data={"username": "admin", "password": "secret"}
    )
    return response.json()["access_token"]


def get_auth_headers():
    """Helper function to get authentication headers."""
    token = get_auth_token()
    return {"Authorization": f"Bearer {token}"}


class TestByBitAuth:
    """Test authentication requirements for ByBit endpoints."""
    
    def test_start_requires_auth(self):
        """Test that starting bot requires authentication."""
        response = client.post("/bybit/start")
        assert response.status_code == 401
        assert "detail" in response.json()
    
    def test_stop_requires_auth(self):
        """Test that stopping bot requires authentication."""
        response = client.post("/bybit/stop")
        assert response.status_code == 401
    
    def test_status_requires_auth(self):
        """Test that getting status requires authentication."""
        response = client.get("/bybit/status")
        assert response.status_code == 401
    
    def test_balance_requires_auth(self):
        """Test that getting balance requires authentication."""
        response = client.get("/bybit/balance")
        assert response.status_code == 401
    
    def test_stats_requires_auth(self):
        """Test that getting stats requires authentication."""
        response = client.get("/bybit/stats")
        assert response.status_code == 401


class TestByBitStatus:
    """Test ByBit status endpoint."""
    
    def test_status_not_initialized(self):
        """Test getting status when bot is not initialized."""
        headers = get_auth_headers()
        
        response = client.get("/bybit/status", headers=headers)
        assert response.status_code == 200
        data = response.json()
        assert data["exchange"] == "bybit"
        # Should return not_initialized since we haven't started the bot
        assert data["status"] == "not_initialized"


class TestByBitBalance:
    """Test ByBit balance endpoint."""
    
    def test_balance_not_initialized(self):
        """Test getting balance when bot is not initialized."""
        headers = get_auth_headers()
        
        response = client.get("/bybit/balance", headers=headers)
        # Should fail since bot is not initialized
        assert response.status_code == 400
        assert "not initialized" in response.json()["detail"].lower()


class TestByBitStats:
    """Test ByBit stats endpoint."""
    
    def test_stats_not_initialized(self):
        """Test getting stats when bot is not initialized."""
        headers = get_auth_headers()
        
        response = client.get("/bybit/stats", headers=headers)
        # Should fail since bot is not initialized
        assert response.status_code == 400
        assert "not initialized" in response.json()["detail"].lower()


class TestByBitStop:
    """Test ByBit stop endpoint."""
    
    def test_stop_not_running(self):
        """Test stopping bot when it's not running."""
        headers = get_auth_headers()
        
        response = client.post("/bybit/stop", headers=headers)
        # Should fail since bot is not running
        assert response.status_code == 400
        assert "not running" in response.json()["detail"].lower()

