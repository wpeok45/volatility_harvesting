"""
Crypto.com exchange API routes (placeholder)
"""
from fastapi import APIRouter, HTTPException, Depends

from .dependencies import traders
from .auth import get_current_user
from .models import User

router = APIRouter(prefix="/cryptocom", tags=["Crypto.com"])


@router.get("/info")
async def cryptocom_info(current_user: User = Depends(get_current_user)):
    """Crypto.com module information (requires authentication)"""
    return {
        "exchange": "cryptocom",
        "status": "not_implemented",
        "message": "Crypto.com trading module will be added soon",
        "enabled": traders["cryptocom"]["enabled"],
    }


@router.post("/start")
async def start_cryptocom_trading(current_user: User = Depends(get_current_user)):
    """Start Crypto.com trading bot (not yet implemented, requires authentication)"""
    raise HTTPException(
        status_code=501,
        detail="Crypto.com trading module is not yet implemented. Coming soon!",
    )


@router.post("/stop")
async def stop_cryptocom_trading(current_user: User = Depends(get_current_user)):
    """Stop Crypto.com trading bot (not yet implemented, requires authentication)"""
    raise HTTPException(
        status_code=501,
        detail="Crypto.com trading module is not yet implemented. Coming soon!",
    )


@router.get("/status")
async def get_cryptocom_status(current_user: User = Depends(get_current_user)):
    """Get Crypto.com bot status (not yet implemented, requires authentication)"""
    raise HTTPException(
        status_code=501,
        detail="Crypto.com trading module is not yet implemented. Coming soon!",
    )
