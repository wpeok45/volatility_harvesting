"""
Pydantic models for API requests and responses
"""
from typing import Optional, List, Dict, Any
from pydantic import BaseModel, Field


# ==================== Authentication Models ====================

class Token(BaseModel):
    """Token response model"""
    access_token: str = Field(default=..., examples=["eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9..."])
    token_type: str = Field(default=..., examples=["bearer"])


class TokenData(BaseModel):
    """Token data model"""
    username: Optional[str] = Field(default=None, examples=["admin"])


class User(BaseModel):
    """User model"""
    username: str = Field(default=..., examples=["admin"])


# ==================== Main API Models ====================

class ExchangeStatus(BaseModel):
    """Exchange status model"""
    enabled: bool = Field(default=..., examples=[True])
    status: str = Field(default=..., examples=["running"])
    name: str = Field(default=..., examples=["ByBit Exchange"])


class RootResponse(BaseModel):
    """Root endpoint response model"""
    message: str = Field(default=..., examples=["Multi-Exchange Volatility Harvesting Trading Bot API"])
    version: str = Field(default=..., examples=["2.0.0"])
    authentication: Dict[str, Any] = Field(default=..., examples=[{
        "required": True,
        "type": "OAuth2 Password Bearer",
        "token_endpoint": "/token",
        "docs": "Use /docs to test authentication interactively"
    }])
    exchanges: Dict[str, ExchangeStatus]
    endpoints: Dict[str, Any]


class ExchangeInfo(BaseModel):
    """Exchange information model"""
    id: str = Field(default=..., examples=["bybit"])
    name: str = Field(default=..., examples=["ByBit Exchange"])
    enabled: bool = Field(default=..., examples=[True])
    running: bool = Field(default=..., examples=[True])
    has_instance: bool = Field(default=..., examples=[True])
    is_started: bool = Field(default=..., examples=[True])


class ExchangesResponse(BaseModel):
    """Exchanges list response model"""
    exchanges: List[ExchangeInfo]


# ==================== Trading Bot Response Models ====================

class StartResponse(BaseModel):
    """Response model for start endpoint"""
    message: str = Field(default=..., examples=["ByBit trading bot started successfully"])
    exchange: str = Field(default=..., examples=["bybit"])
    status: str = Field(default=..., examples=["running"])
    is_started: bool = Field(default=..., examples=[True])


class StopResponse(BaseModel):
    """Response model for stop endpoint"""
    message: str = Field(default=..., examples=["ByBit trading bot stopped successfully"])
    exchange: str = Field(default=..., examples=["bybit"])
    status: str = Field(default=..., examples=["stopped"])
    is_started: bool = Field(default=..., examples=[False])


class StatusResponse(BaseModel):
    """Response model for status endpoint"""
    exchange: str = Field(default=..., examples=["bybit"])
    status: str = Field(default=..., examples=["running"])
    is_started: bool = Field(default=..., examples=[True])
    symbol: Optional[str] = Field(default=None, examples=["BTCUSDC"])
    ratio: Optional[float] = Field(default=None, examples=[0.45])
    range: Optional[float] = Field(default=None, examples=[50000.0])
    ma_length: Optional[int] = Field(default=None, examples=[24])
    rebalance_top: Optional[float] = Field(default=None, examples=[3.0])
    rebalance_bottom: Optional[float] = Field(default=None, examples=[3.0])
    message: Optional[str] = Field(default=None, examples=["Bot is actively trading"])


class BalanceInfo(BaseModel):
    """Balance information model"""
    coin: str = Field(default=..., examples=["BTC"])
    balance: float = Field(default=..., examples=[0.15234567])
    usd_value: float = Field(default=..., examples=[15234.56])


class BalanceResponse(BaseModel):
    """Response model for balance endpoint"""
    exchange: str = Field(default=..., examples=["bybit"])
    balances: List[BalanceInfo] = Field(default=..., examples=[[
        {"coin": "BTC", "balance": 0.15234567, "usd_value": 15234.56},
        {"coin": "USDC", "balance": 15234.56, "usd_value": 15234.56}
    ]])
    total_usd: float = Field(default=..., examples=[30469.12])


class TradeInfo(BaseModel):
    """Trade information model"""
    side: str = Field(default=..., examples=["buy"])
    price: float = Field(default=..., examples=[98765.43])
    quantity: float = Field(default=..., examples=[0.01234567])
    timestamp: str = Field(default=..., examples=["2025-10-20 12:34:56"])


class StatsResponse(BaseModel):
    """Response model for stats endpoint"""
    exchange: str = Field(default=..., examples=["bybit"])
    symbol: str = Field(default=..., examples=["BTCUSDC"])
    last_price: Optional[float] = Field(default=None, examples=[98765.43])
    traded_price: Optional[float] = Field(default=None, examples=[98500.00])
    buy_price_mean: Optional[float] = Field(default=None, examples=[97800.50])
    trade_profit: Optional[float] = Field(default=None, examples=[1234.56])
    percent_diff: Optional[float] = Field(default=None, examples=[1.5])
    price_diff: Optional[float] = Field(default=None, examples=[265.43])
    portfolio_ratio: Optional[float] = Field(default=None, examples=[45.0])
    real_ratio: Optional[float] = Field(default=None, examples=[0.45])
    ATH: Optional[float] = Field(default=None, examples=[100000.0])
    work_range: Optional[float] = Field(default=None, examples=[50000.0])
    local_range: Optional[float] = Field(default=None, examples=[5000.0])
    rebalance_top: Optional[float] = Field(default=None, examples=[3.0])
    rebalance_bottom: Optional[float] = Field(default=None, examples=[3.0])
    min_profitable_percent: Optional[float] = Field(default=None, examples=[0.2])
    order_scale: Optional[Dict[str, Any]] = Field(default=None, examples=[{
        "enabled": True,
        "buy_counter": 2,
        "sell_counter": 1,
        "buy_percent": 1.5,
        "sell_percent": 3.0
    }])
    impuls: Optional[float] = Field(default=None, examples=[500.0])
    impuls_percent: Optional[float] = Field(default=None, examples=[0.5])
