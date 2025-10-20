"""
Shared dependencies for API routers
"""
import asyncio
from typing import Dict, Any, Optional
from pathlib import Path

# Global variables for managing multiple exchange traders
traders: Dict[str, Dict[str, Any]] = {
    "bybit": {
        "instance": None,
        "task": None,
        "tasks": [],
        "enabled": True,
        "name": "ByBit Spot",
        "is_started": True
    },
    "binance": {
        "instance": None,
        "task": None,
        "tasks": [],
        "enabled": False,
        "name": "Binance Spot",
        "is_started": False
    },
    "cryptocom": {
        "instance": None,
        "task": None,
        "tasks": [],
        "enabled": False,
        "name": "Crypto.com Spot",
        "is_started": False
    }
}

main_loop: Optional[asyncio.AbstractEventLoop] = None

def get_main_loop() -> Optional[asyncio.AbstractEventLoop]:
    """Get current main loop"""
    return main_loop

def set_main_loop(loop: asyncio.AbstractEventLoop):
    """Set main loop"""
    global main_loop
    main_loop = loop

# Data directories for each exchange
DATA_DIR = Path("data")
EXCHANGE_DATA_DIRS = {
    "bybit": DATA_DIR / "bybit",
    "binance": DATA_DIR / "binance",
    "cryptocom": DATA_DIR / "cryptocom"
}

# Ensure data directories exist
for exchange_dir in EXCHANGE_DATA_DIRS.values():
    exchange_dir.mkdir(parents=True, exist_ok=True)
