"""
Crypto.com exchange API routes (placeholder)
"""
from fastapi import APIRouter, HTTPException

from .dependencies import traders

router = APIRouter(prefix="/cryptocom", tags=["Crypto.com"])


@router.get("/info")
async def cryptocom_info():
    """Crypto.com module information"""
    return {
        "exchange": "cryptocom",
        "status": "not_implemented",
        "message": "Crypto.com trading module will be added soon",
        "enabled": traders["cryptocom"]["enabled"]
    }


@router.post("/start")
async def start_cryptocom_trading():
    """Start Crypto.com trading bot (not yet implemented)"""
    raise HTTPException(
        status_code=501,
        detail="Crypto.com trading module is not yet implemented. Coming soon!"
    )


@router.post("/stop")
async def stop_cryptocom_trading():
    """Stop Crypto.com trading bot (not yet implemented)"""
    raise HTTPException(
        status_code=501,
        detail="Crypto.com trading module is not yet implemented. Coming soon!"
    )


@router.get("/status")
async def get_cryptocom_status():
    """Get Crypto.com bot status (not yet implemented)"""
    raise HTTPException(
        status_code=501,
        detail="Crypto.com trading module is not yet implemented. Coming soon!"
    )
