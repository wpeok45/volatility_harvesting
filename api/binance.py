"""
Binance exchange API routes (placeholder)
"""
from fastapi import APIRouter, HTTPException

from .dependencies import traders

router = APIRouter(prefix="/binance", tags=["Binance"])


@router.get("/info")
async def binance_info():
    """Binance module information"""
    return {
        "exchange": "binance",
        "status": "not_implemented",
        "message": "Binance trading module will be added soon",
        "enabled": traders["binance"]["enabled"]
    }


@router.post("/start")
async def start_binance_trading():
    """Start Binance trading bot (not yet implemented)"""
    raise HTTPException(
        status_code=501,
        detail="Binance trading module is not yet implemented. Coming soon!"
    )


@router.post("/stop")
async def stop_binance_trading():
    """Stop Binance trading bot (not yet implemented)"""
    raise HTTPException(
        status_code=501,
        detail="Binance trading module is not yet implemented. Coming soon!"
    )


@router.get("/status")
async def get_binance_status():
    """Get Binance bot status (not yet implemented)"""
    raise HTTPException(
        status_code=501,
        detail="Binance trading module is not yet implemented. Coming soon!"
    )
