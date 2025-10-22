"""
Simple pytest test for root endpoint.
"""
from fastapi.testclient import TestClient
from api_main import app


client = TestClient(app)


def test_read_root():
    """Test root endpoint returns welcome message."""
    response = client.get("/")
    assert response.status_code == 200
    data = response.json()
    assert "message" in data
    assert "Volatility Harvesting" in data["message"]
    assert "API" in data["message"]


def test_exchanges_requires_auth():
    """Test exchanges endpoint requires authentication."""
    response = client.get("/exchanges")
    assert response.status_code == 401
    assert "detail" in response.json()

