"""
Binance exchange API routes (placeholder)
"""
from fastapi import APIRouter, HTTPException, Depends

from .dependencies import traders
from .auth import get_current_user, User

router = APIRouter(prefix="/binance", tags=["Binance"])


@router.get("/info")
async def binance_info(current_user: User = Depends(get_current_user)):
    """Binance module information (requires authentication)"""
    return {
        "exchange": "binance",
        "status": "not_implemented",
        "message": "Binance trading module will be added soon",
        "enabled": traders["binance"]["enabled"]
    }


@router.post("/start")
async def start_binance_trading(current_user: User = Depends(get_current_user)):
    """Start Binance trading bot (not yet implemented, requires authentication)"""
    raise HTTPException(
        status_code=501,
        detail="Binance trading module is not yet implemented. Coming soon!"
    )


@router.post("/stop")
async def stop_binance_trading(current_user: User = Depends(get_current_user)):
    """Stop Binance trading bot (not yet implemented, requires authentication)"""
    raise HTTPException(
        status_code=501,
        detail="Binance trading module is not yet implemented. Coming soon!"
    )


@router.get("/status")
async def get_binance_status(current_user: User = Depends(get_current_user)):
    """Get Binance bot status (not yet implemented, requires authentication)"""
    raise HTTPException(
        status_code=501,
        detail="Binance trading module is not yet implemented. Coming soon!"
    )

