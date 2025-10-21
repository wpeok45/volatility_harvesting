"""
Pytest configuration file for volatility harvesting tests.

This file contains fixtures following the fastapi/full-stack-fastapi-template pattern.
All tests run without starting the real API server using TestClient.

Key principles:
1. Use TestClient for synchronous API testing
2. Use mocks to simulate trader behavior
3. Clean up state between tests
4. Module-scoped fixtures for client and auth headers

Available Fixtures:
- client: TestClient for API testing (module scope)
- superuser_token_headers: Admin authentication headers (module scope)
- mock_trader: Mock trader instance (function scope)
- reset_traders: Cleanup fixture (autouse, function scope)
"""
import os
from collections.abc import Generator
from typing import Dict
from unittest.mock import AsyncMock, MagicMock

import pytest
from fastapi.testclient import TestClient

# Set test environment variables BEFORE importing app
os.environ["TESTING"] = "true"
os.environ["ADMIN_USERNAME"] = "admin"
os.environ["ADMIN_PASSWORD"] = "secret"
os.environ["JWT_SECRET_KEY"] = "test_secret_key_for_testing_only_do_not_use_in_production"
os.environ["API_KEY"] = "test_api_key"
os.environ["SECRET_KEY"] = "test_secret_key"

from api_main import app  # noqa: E402
from tests.utils.utils import get_superuser_token_headers  # noqa: E402


@pytest.fixture(scope="module")
def client() -> Generator[TestClient, None, None]:
    """
    Create a test client for API testing.
    
    Uses module scope to reuse the same client across tests in a module.
    TestClient automatically handles the app lifecycle without running lifespan events.
    
    Yields:
        TestClient instance
    """
    with TestClient(app) as c:
        yield c


@pytest.fixture(scope="module")
def superuser_token_headers(client: TestClient) -> Dict[str, str]:
    """
    Get authentication headers for superuser.
    
    Args:
        client: TestClient instance
        
    Returns:
        Dictionary with Authorization header
    """
    return get_superuser_token_headers(client)





@pytest.fixture(scope="function")
def mock_trader() -> MagicMock:
    """
    Create a mock trader instance for testing.
    
    Returns:
        Mock trader with common methods mocked
    """
    mock = MagicMock()
    mock.state = "stopped"
    mock.exchange_name = "bybit"
    mock.symbol = "BTCUSDC"
    mock.interval = 60
    mock.stop = AsyncMock()
    mock.get_status = MagicMock(return_value={
        "state": "stopped",
        "symbol": "BTCUSDC",
        "exchange": "bybit",
        "interval": 60
    })
    mock.get_balance = MagicMock(return_value={
        "USDC": {"free": 10000.0, "used": 0.0, "total": 10000.0}
    })
    mock.get_stats = MagicMock(return_value={
        "total_pnl": 150.5,
        "num_trades": 10,
        "win_rate": 0.6,
        "sharpe_ratio": 1.5
    })
    return mock


@pytest.fixture(autouse=True)
def reset_traders():
    """
    Reset trader instances between tests.
    
    This fixture runs automatically after each test to ensure test isolation.
    """
    from api import bybit
    
    yield
    
    # Clean up after test
    if hasattr(bybit, 'traders'):
        bybit.traders.clear()
