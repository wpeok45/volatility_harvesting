"""Helper functions for trader-related tests."""
from typing import Dict, Any
from unittest.mock import AsyncMock, MagicMock


def create_mock_trader() -> MagicMock:
    """Create a mock trader instance for testing."""
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


def create_start_response() -> Dict[str, Any]:
    """Create a mock start response."""
    return {
        "message": "ByBit trader started successfully",
        "symbol": "BTCUSDC",
        "interval": 60,
        "initial_balance": {
            "USDC": {"free": 10000.0, "used": 0.0, "total": 10000.0}
        }
    }


def create_status_response(state: str = "running") -> Dict[str, Any]:
    """Create a mock status response."""
    return {
        "exchange": "bybit",
        "state": state,
        "symbol": "BTCUSDC",
        "interval": 60,
        "uptime": 3600.5
    }


def create_balance_response() -> Dict[str, Any]:
    """Create a mock balance response."""
    return {
        "exchange": "bybit",
        "balances": {
            "USDC": {"free": 10000.0, "used": 0.0, "total": 10000.0},
            "BTC": {"free": 0.5, "used": 0.0, "total": 0.5}
        },
        "total_value_usdc": 10000.0
    }


def create_stats_response() -> Dict[str, Any]:
    """Create a mock stats response."""
    return {
        "exchange": "bybit",
        "symbol": "BTCUSDC",
        "total_trades": 10,
        "winning_trades": 6,
        "losing_trades": 4,
        "win_rate": 0.6,
        "total_pnl": 150.5,
        "sharpe_ratio": 1.5,
        "max_drawdown": 50.0,
        "avg_trade_duration": 3600
    }
