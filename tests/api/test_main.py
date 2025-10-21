"""Tests for main API endpoints."""
from fastapi.testclient import TestClient


def test_read_root(client: TestClient) -> None:
    """Test root endpoint."""
    r = client.get("/")
    assert r.status_code == 200
    response = r.json()
    assert "message" in response
    assert "Volatility Harvesting" in response["message"]


def test_get_exchanges(
    client: TestClient, superuser_token_headers: dict[str, str]
) -> None:
    """Test getting list of available exchanges."""
    r = client.get("/exchanges", headers=superuser_token_headers)
    assert r.status_code == 200
    response = r.json()
    assert "exchanges" in response
    assert isinstance(response["exchanges"], list)
    
    # Check that response contains exchange objects
    if len(response["exchanges"]) > 0:
        exchange = response["exchanges"][0]
        assert "id" in exchange
        assert "name" in exchange
        assert "enabled" in exchange
        assert "running" in exchange
        assert "has_instance" in exchange
        assert "is_started" in exchange


def test_get_exchanges_unauthorized(client: TestClient) -> None:
    """Test getting exchanges without authentication."""
    r = client.get("/exchanges")
    assert r.status_code == 401

