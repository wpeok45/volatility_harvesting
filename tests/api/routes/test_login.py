"""Tests for login endpoints."""
from fastapi.testclient import TestClient


def test_get_access_token(client: TestClient) -> None:
    """Test getting access token with valid credentials."""
    login_data = {
        "username": "admin",
        "password": "secret",
    }
    r = client.post("/token", data=login_data)
    assert r.status_code == 200
    tokens = r.json()
    assert "access_token" in tokens
    assert tokens["token_type"] == "bearer"


def test_get_access_token_incorrect_password(client: TestClient) -> None:
    """Test login with incorrect password."""
    login_data = {
        "username": "admin",
        "password": "wrong_password",
    }
    r = client.post("/token", data=login_data)
    assert r.status_code == 401
    assert r.json()["detail"] == "Incorrect username or password"


def test_get_access_token_incorrect_username(client: TestClient) -> None:
    """Test login with incorrect username."""
    login_data = {
        "username": "wrong_user",
        "password": "secret",
    }
    r = client.post("/token", data=login_data)
    assert r.status_code == 401
    assert r.json()["detail"] == "Incorrect username or password"


def test_use_access_token(
    client: TestClient, superuser_token_headers: dict[str, str]
) -> None:
    """Test using access token to access protected endpoint."""
    # Test root endpoint which requires no special setup
    r = client.get("/", headers=superuser_token_headers)
    # Should not return 401 Unauthorized
    assert r.status_code != 401
    assert r.status_code == 200


def test_access_protected_endpoint_without_token(client: TestClient) -> None:
    """Test accessing protected endpoint without token."""
    # Use exchanges endpoint which requires authentication
    r = client.get("/exchanges")
    assert r.status_code == 401
    assert r.json()["detail"] == "Not authenticated"
