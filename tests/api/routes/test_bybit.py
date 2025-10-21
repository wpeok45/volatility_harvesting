"""Tests for ByBit API endpoints."""
from unittest.mock import MagicMock, patch

from fastapi.testclient import TestClient


def test_start_bybit_trader_unauthorized(client: TestClient) -> None:
    """Test starting trader without authentication."""
    data = {"symbol": "BTCUSDC", "interval": 60}
    r = client.post("/bybit/start", json=data)
    assert r.status_code == 401


def test_start_bybit_trader_disabled(
    client: TestClient, superuser_token_headers: dict[str, str]
) -> None:
    """Test starting trader when module is disabled."""
    # Патчим traders dict чтобы bybit был disabled
    with patch("api.bybit.traders", {"bybit": {"enabled": False, "task": None}}):
        r = client.post(
            "/bybit/start",
            headers=superuser_token_headers,
        )
        
        assert r.status_code == 400
        assert "not enabled" in r.json()["detail"].lower()


def test_start_bybit_trader_already_running(
    client: TestClient, superuser_token_headers: dict[str, str]
) -> None:
    """Test starting trader when it's already running."""
    # Создаем mock task который не done
    mock_task = MagicMock()
    mock_task.done.return_value = False
    
    with patch("api.bybit.traders", {"bybit": {"enabled": True, "task": mock_task}}):
        r = client.post(
            "/bybit/start",
            headers=superuser_token_headers,
        )
        
        assert r.status_code == 400
        assert "already running" in r.json()["detail"].lower()


def test_stop_bybit_trader_unauthorized(client: TestClient) -> None:
    """Test stopping trader without authentication."""
    r = client.post("/bybit/stop")
    assert r.status_code == 401


def test_stop_bybit_trader_not_enabled(
    client: TestClient, superuser_token_headers: dict[str, str]
) -> None:
    """Test stopping trader when module is disabled."""
    with patch("api.bybit.traders", {"bybit": {"enabled": False, "task": None}}):
        r = client.post(
            "/bybit/stop",
            headers=superuser_token_headers,
        )
        
        assert r.status_code == 400
        # API возвращает "not running" когда task is None
        assert "not running" in r.json()["detail"].lower()


def test_stop_bybit_trader_not_running(
    client: TestClient, superuser_token_headers: dict[str, str]
) -> None:
    """Test stopping trader that is not running."""
    with patch("api.bybit.traders", {"bybit": {"enabled": True, "task": None}}):
        r = client.post(
            "/bybit/stop",
            headers=superuser_token_headers,
        )
        
        assert r.status_code == 400
        assert "not running" in r.json()["detail"].lower()


def test_get_bybit_status_unauthorized(client: TestClient) -> None:
    """Test getting status without authentication."""
    r = client.get("/bybit/status")
    assert r.status_code == 401


def test_get_bybit_status_not_enabled(
    client: TestClient, superuser_token_headers: dict[str, str]
) -> None:
    """Test getting status when module is disabled."""
    # Mock должен содержать все необходимые ключи
    mock_traders = {
        "bybit": {
            "enabled": False,
            "instance": None,
            "name": "ByBit",
            "is_started": False,
            "task": None,
            "tasks": []
        }
    }
    with patch("api.bybit.traders", mock_traders):
        r = client.get(
            "/bybit/status",
            headers=superuser_token_headers,
        )
        
        # API возвращает 200 с status not_initialized
        assert r.status_code == 200
        response = r.json()
        assert response["status"] == "not_initialized"
        assert response["exchange"] == "bybit"


def test_get_bybit_status_no_instance(
    client: TestClient, superuser_token_headers: dict[str, str]
) -> None:
    """Test getting status when no instance exists."""
    # Mock должен содержать все необходимые ключи
    mock_traders = {
        "bybit": {
            "enabled": True,
            "instance": None,
            "name": "ByBit",
            "is_started": False,
            "task": None,
            "tasks": []
        }
    }
    with patch("api.bybit.traders", mock_traders):
        r = client.get(
            "/bybit/status",
            headers=superuser_token_headers,
        )
        
        # API возвращает 200 с status not_initialized
        assert r.status_code == 200
        response = r.json()
        assert response["status"] == "not_initialized"
        assert response["exchange"] == "bybit"
        assert "not been started yet" in response["message"].lower()


def test_get_bybit_balance_unauthorized(client: TestClient) -> None:
    """Test getting balance without authentication."""
    r = client.get("/bybit/balance")
    assert r.status_code == 401


def test_get_bybit_balance_not_enabled(
    client: TestClient, superuser_token_headers: dict[str, str]
) -> None:
    """Test getting balance when module is disabled."""
    with patch("api.bybit.traders", {"bybit": {"enabled": False, "instance": None}}):
        r = client.get(
            "/bybit/balance",
            headers=superuser_token_headers,
        )
        
        # API возвращает 400 с "not initialized" когда instance is None
        assert r.status_code == 400
        assert "not initialized" in r.json()["detail"].lower()


def test_get_bybit_balance_no_instance(
    client: TestClient, superuser_token_headers: dict[str, str]
) -> None:
    """Test getting balance when no instance exists."""
    with patch("api.bybit.traders", {"bybit": {"enabled": True, "instance": None}}):
        r = client.get(
            "/bybit/balance",
            headers=superuser_token_headers,
        )
        
        # API возвращает 400 вместо 500
        assert r.status_code == 400
        assert "not initialized" in r.json()["detail"].lower()


def test_get_bybit_stats_unauthorized(client: TestClient) -> None:
    """Test getting stats without authentication."""
    r = client.get("/bybit/stats")
    assert r.status_code == 401


def test_get_bybit_stats_not_enabled(
    client: TestClient, superuser_token_headers: dict[str, str]
) -> None:
    """Test getting stats when module is disabled."""
    with patch("api.bybit.traders", {"bybit": {"enabled": False, "instance": None}}):
        r = client.get(
            "/bybit/stats",
            headers=superuser_token_headers,
        )
        
        # API возвращает 400 с "not initialized"
        assert r.status_code == 400
        assert "not initialized" in r.json()["detail"].lower()


def test_get_bybit_stats_no_instance(
    client: TestClient, superuser_token_headers: dict[str, str]
) -> None:
    """Test getting stats when no instance exists."""
    with patch("api.bybit.traders", {"bybit": {"enabled": True, "instance": None}}):
        r = client.get(
            "/bybit/stats",
            headers=superuser_token_headers,
        )
        
        # API возвращает 400 вместо 500
        assert r.status_code == 400
        assert "not initialized" in r.json()["detail"].lower()
