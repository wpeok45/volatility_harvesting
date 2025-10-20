"""
ByBit exchange API routes
"""
import asyncio
from fastapi import APIRouter, HTTPException, Depends
from fastapi.responses import JSONResponse

from .dependencies import traders, get_main_loop, EXCHANGE_DATA_DIRS
from .auth import get_current_user, User
from vh_float import Trader as ByBitSpotTrader, API_KEY as BYBIT_API_KEY, SECRET_KEY as BYBIT_SECRET_KEY

router = APIRouter(prefix="/bybit", tags=["ByBit"])


async def start_bybit_internal():
    """Internal function to start ByBit bot (used for auto-start)"""
    main_loop = get_main_loop()
    
    if not traders["bybit"]["enabled"]:
        print("ByBit module is not enabled, skipping auto-start")
        return False
    
    if traders["bybit"]["task"] and not traders["bybit"]["task"].done():
        print("ByBit trading bot is already running")
        return False
    
    if main_loop is None:
        print("Event loop not initialized")
        return False
    
    try:
        # Create ByBit trader instance with data directory
        data_dir = str(EXCHANGE_DATA_DIRS["bybit"])
        trader_instance = ByBitSpotTrader(
            loop=main_loop, 
            key=BYBIT_API_KEY, 
            secret=BYBIT_SECRET_KEY,
            data_dir=data_dir
        )
        traders["bybit"]["instance"] = trader_instance
        
        # Initialize trader data
        await trader_instance.init_data()
        
        # Clear old tasks list
        traders["bybit"]["tasks"] = []
        
        # Start websocket connections and trading tasks - track all tasks
        task1 = asyncio.create_task(trader_instance.ws_ticker())
        traders["bybit"]["tasks"].append(task1)
        
        await asyncio.sleep(1.0)
        
        task2 = asyncio.create_task(trader_instance.ws_user_data())
        traders["bybit"]["tasks"].append(task2)
        
        task3 = asyncio.create_task(trader_instance.account_balance_loop())
        traders["bybit"]["tasks"].append(task3)
        
        task4 = asyncio.create_task(trader_instance.save_history_loop())
        traders["bybit"]["tasks"].append(task4)
        
        # Start main trading loop
        traders["bybit"]["task"] = asyncio.create_task(trader_instance.trade_loop())
        
        print(f"ByBit trading bot auto-started successfully (symbol: {trader_instance.symbol})")
        return True
    except Exception as e:
        print(f"Failed to auto-start ByBit trading bot: {str(e)}")
        return False


@router.post("/start")
async def start_bybit_trading(current_user: User = Depends(get_current_user)):
    """Start the ByBit trading bot (requires authentication)"""
    from .config import save_api_config
    
    main_loop = get_main_loop()
    
    if not traders["bybit"]["enabled"]:
        raise HTTPException(status_code=400, detail="ByBit module is not enabled")
    
    if traders["bybit"]["task"] and not traders["bybit"]["task"].done():
        raise HTTPException(status_code=400, detail="ByBit trading bot is already running")
    
    if main_loop is None:
        raise HTTPException(status_code=500, detail="Event loop not initialized")
    
    try:
        # Create ByBit trader instance with data directory
        data_dir = str(EXCHANGE_DATA_DIRS["bybit"])
        trader_instance = ByBitSpotTrader(
            loop=main_loop, 
            key=BYBIT_API_KEY, 
            secret=BYBIT_SECRET_KEY,
            data_dir=data_dir
        )
        traders["bybit"]["instance"] = trader_instance
        
        # Initialize trader data
        await trader_instance.init_data()
        
        # Clear old tasks list
        traders["bybit"]["tasks"] = []
        
        # Start websocket connections and trading tasks - track all tasks
        task1 = asyncio.create_task(trader_instance.ws_ticker())
        traders["bybit"]["tasks"].append(task1)
        
        await asyncio.sleep(1.0)
        
        task2 = asyncio.create_task(trader_instance.ws_user_data())
        traders["bybit"]["tasks"].append(task2)
        
        task3 = asyncio.create_task(trader_instance.account_balance_loop())
        traders["bybit"]["tasks"].append(task3)
        
        task4 = asyncio.create_task(trader_instance.save_history_loop())
        traders["bybit"]["tasks"].append(task4)
        
        # Start main trading loop
        traders["bybit"]["task"] = asyncio.create_task(trader_instance.trade_loop())
        
        # Update is_started flag and save config
        traders["bybit"]["is_started"] = True
        save_api_config()
        
        return JSONResponse(
            status_code=200,
            content={
                "exchange": "bybit",
                "message": "ByBit trading bot started successfully",
                "symbol": trader_instance.symbol,
                "status": "running",
                "is_started": True
            }
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to start ByBit trading bot: {str(e)}")


@router.post("/stop")
async def stop_bybit_trading(current_user: User = Depends(get_current_user)):
    """Stop the ByBit trading bot (requires authentication)"""
    from .config import save_api_config
    
    trader_task = traders["bybit"]["task"]
    
    if not trader_task or trader_task.done():
        raise HTTPException(status_code=400, detail="ByBit trading bot is not running")
    
    try:
        # Cancel main trading loop
        trader_task.cancel()
        await trader_task
    except asyncio.CancelledError:
        pass
    
    # Cancel all background tasks (websockets, balance loop, save history)
    if traders["bybit"]["tasks"]:
        print(f"Stopping {len(traders['bybit']['tasks'])} background tasks...")
        for task in traders["bybit"]["tasks"]:
            if not task.done():
                task.cancel()
                try:
                    await task
                except asyncio.CancelledError:
                    pass
        traders["bybit"]["tasks"] = []
        print("All ByBit background tasks stopped")
    
    # Update is_started flag and save config
    traders["bybit"]["is_started"] = False
    save_api_config()
    
    return JSONResponse(
        status_code=200,
        content={
            "exchange": "bybit",
            "message": "ByBit trading bot stopped successfully",
            "status": "stopped",
            "is_started": False
        }
    )


@router.get("/status")
async def get_bybit_status(current_user: User = Depends(get_current_user)):
    """Get current ByBit trading bot status (requires authentication)"""
    trader_instance = traders["bybit"]["instance"]
    
    if not trader_instance:
        return {
            "exchange": "bybit",
            "status": "not_initialized",
            "is_started": traders["bybit"]["is_started"],
            "message": "ByBit trading bot has not been started yet"
        }
    
    is_running = traders["bybit"]["task"] and not traders["bybit"]["task"].done()
    
    status_info = {
        "exchange": "bybit",
        "status": "running" if is_running else "stopped",
        "is_started": traders["bybit"]["is_started"],
        "symbol": trader_instance.symbol,
        "last_price": trader_instance.last_price,
        "portfolio_ratio": round(trader_instance.ta.portfolio_ratio * 100, 2),
        "real_ratio": trader_instance.ta.real_ratio,
        "ATH": trader_instance.ta.ATH,
        "work_range": trader_instance.ta.work_range,
        "local_range": trader_instance.ta.local_range,
        "ma_trend": trader_instance.ta.ma_trend,
        "ma_fast": trader_instance.ta.ma_fast_m,
    }
    
    return status_info


@router.get("/balance")
async def get_bybit_balance(current_user: User = Depends(get_current_user)):
    """Get current ByBit account balance (requires authentication)"""
    trader_instance = traders["bybit"]["instance"]
    
    if not trader_instance:
        raise HTTPException(status_code=400, detail="ByBit trading bot not initialized")
    
    await trader_instance.get_account_balance()
    
    return {
        "exchange": "bybit",
        "native_balance": {
            trader_instance.pair[0]: trader_instance.ta.native_balance[0],
            trader_instance.pair[1]: trader_instance.ta.native_balance[1]
        },
        "pair_balance": trader_instance.ta.pair_balance,
        "real_ratio": trader_instance.ta.real_ratio,
        "last_price": trader_instance.last_price
    }


@router.get("/stats")
async def get_bybit_stats(current_user: User = Depends(get_current_user)):
    """Get ByBit trading statistics (requires authentication)"""
    trader_instance = traders["bybit"]["instance"]
    
    if not trader_instance:
        raise HTTPException(status_code=400, detail="ByBit trading bot not initialized")
    
    return {
        "exchange": "bybit",
        "symbol": trader_instance.symbol,
        "last_price": trader_instance.last_price,
        "traded_price": trader_instance.ta.traded_price,
        "buy_price_mean": trader_instance.ta.buy_price_mean,
        "trade_profit": trader_instance.ta.trade_profit,
        "percent_diff": trader_instance.ta.percent_diff,
        "price_diff": trader_instance.ta.price_diff,
        "portfolio_ratio": round(trader_instance.ta.portfolio_ratio * 100, 2),
        "real_ratio": trader_instance.ta.real_ratio,
        "ATH": trader_instance.ta.ATH,
        "work_range": trader_instance.ta.work_range,
        "local_range": trader_instance.ta.local_range,
        "rebalance_top": trader_instance.ta.rebalance_top,
        "rebalance_bottom": trader_instance.ta.rebalance_bottom,
        "min_profitable_percent": trader_instance.ta.min_profitable_percent,
        "order_scale": {
            "enabled": trader_instance.ta.order_scale.enabled,
            "buy_counter": trader_instance.ta.order_scale.buy_counter,
            "sell_counter": trader_instance.ta.order_scale.sell_counter,
            "buy_percent": trader_instance.ta.order_scale.get_buy_percent(),
            "sell_percent": trader_instance.ta.order_scale.get_sell_percent()
        },
        "impuls": trader_instance.ta.impuls,
        "impuls_percent": trader_instance.ta.impuls_percent,
        "impuls_harmonic": trader_instance.ta.impuls_harmonic,
        "impuls_harmonic_percent": trader_instance.ta.impuls_harmonic_percent,
        "ma_trend": trader_instance.ta.ma_trend,
        "ma_fast": trader_instance.ta.ma_fast_m
    }
