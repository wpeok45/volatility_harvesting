import asyncio
from contextlib import asynccontextmanager
from typing import Dict, Optional, List
import json
import os
from pathlib import Path as FilePath
from fastapi import FastAPI, HTTPException, Path
from fastapi.responses import JSONResponse
import uvicorn

# Import the Trader class from vh_float (ByBit)
from vh_float import Trader as ByBitSpotTrader, API_KEY as BYBIT_API_KEY, SECRET_KEY as BYBIT_SECRET_KEY

# TODO: Import Binance trader when module is ready
# from binance_trader import Trader as BinanceSpotTrader, API_KEY as BINANCE_API_KEY, SECRET_KEY as BINANCE_SECRET_KEY

# TODO: Import Crypto.com trader when module is ready
# from cryptocom_trader import Trader as CryptocomSpotTrader, API_KEY as CRYPTOCOM_API_KEY, SECRET_KEY as CRYPTOCOM_SECRET_KEY

# Configuration file for API settings
API_CONFIG_FILE = "api_config.json"

# Global variables for managing multiple exchange traders
from typing import Any
traders: Dict[str, Dict[str, Any]] = {
    "bybit": {
        "instance": None,
        "task": None,  # Main trade_loop task
        "tasks": [],  # All background tasks (websockets, loops)
        "enabled": True,
        "name": "ByBit Spot",
        "is_started": True  # Auto-start by default
    },
    "binance": {
        "instance": None,
        "task": None,
        "tasks": [],
        "enabled": False,  # Will be enabled when Binance module is added
        "name": "Binance Spot",
        "is_started": False
    },
    "cryptocom": {
        "instance": None,
        "task": None,
        "tasks": [],
        "enabled": False,  # Will be enabled when Crypto.com module is added
        "name": "Crypto.com Spot",
        "is_started": False
    }
}

main_loop = None


def save_api_config():
    """Save API settings to JSON file"""
    config = {}
    for exchange, data in traders.items():
        config[exchange] = {
            "enabled": data["enabled"],
            "is_started": data["is_started"],
            "name": data["name"]
        }
    
    try:
        with open(API_CONFIG_FILE, 'w') as f:
            json.dump(config, f, indent=2)
        print(f"API configuration saved to {API_CONFIG_FILE}")
    except Exception as e:
        print(f"Error saving API configuration: {e}")


def load_api_config():
    """Load API settings from JSON file"""
    if not os.path.exists(API_CONFIG_FILE):
        print(f"No configuration file found at {API_CONFIG_FILE}, using defaults")
        return
    
    try:
        with open(API_CONFIG_FILE, 'r') as f:
            config = json.load(f)
        
        for exchange, settings in config.items():
            if exchange in traders:
                traders[exchange]["enabled"] = settings.get("enabled", traders[exchange]["enabled"])
                traders[exchange]["is_started"] = settings.get("is_started", traders[exchange]["is_started"])
                traders[exchange]["name"] = settings.get("name", traders[exchange]["name"])
        
        print(f"API configuration loaded from {API_CONFIG_FILE}")
    except Exception as e:
        print(f"Error loading API configuration: {e}")


async def start_bybit_internal():
    """Internal function to start ByBit bot (used for auto-start)"""
    global traders, main_loop
    
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
        # Create ByBit trader instance
        trader_instance = ByBitSpotTrader(loop=main_loop, key=BYBIT_API_KEY, secret=BYBIT_SECRET_KEY)
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


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Manage the lifecycle of all trading bots"""
    global traders, main_loop
    
    print("Starting Multi-Exchange Volatility Harvesting API...")
    
    # Load saved configuration
    load_api_config()
    
    # Initialize event loop
    main_loop = asyncio.get_running_loop()
    
    # Auto-start exchanges that have is_started=True
    await asyncio.sleep(0.5)  # Small delay for initialization
    
    for exchange, data in traders.items():
        if data["enabled"] and data["is_started"]:
            print(f"Auto-starting {exchange} trader...")
            if exchange == "bybit":
                await start_bybit_internal()
            # TODO: Add auto-start for other exchanges when modules are ready
    
    yield
    
    # Save configuration before shutdown
    save_api_config()
    
    # Cleanup on shutdown
    print("Shutting down all trading bots...")
    for exchange_name, trader_data in traders.items():
        if trader_data["task"] and not trader_data["task"].done():
            print(f"Stopping {exchange_name} trader...")
            
            # Cancel main task
            trader_data["task"].cancel()
            try:
                await trader_data["task"]
            except asyncio.CancelledError:
                print(f"{exchange_name} main task cancelled")
            
            # Cancel all background tasks (websockets, loops)
            if trader_data["tasks"]:
                print(f"Stopping {len(trader_data['tasks'])} background tasks for {exchange_name}...")
                for task in trader_data["tasks"]:
                    if not task.done():
                        task.cancel()
                        try:
                            await task
                        except asyncio.CancelledError:
                            pass
                print(f"{exchange_name} all tasks stopped successfully")


app = FastAPI(
    title="Multi-Exchange Volatility Harvesting Bot",
    description="API for managing cryptocurrency volatility harvesting across multiple exchanges (ByBit, Binance, Crypto.com)",
    version="2.0.0",
    lifespan=lifespan
)


# ==================== ROOT ENDPOINTS ====================

@app.get("/")
async def root():
    """Root endpoint with API overview"""
    return {
        "message": "Multi-Exchange Volatility Harvesting Trading Bot API",
        "version": "2.0.0",
        "exchanges": {
            name: {
                "enabled": data["enabled"],
                "status": "running" if data["task"] and not data["task"].done() else "stopped",
                "name": data["name"]
            }
            for name, data in traders.items()
        },
        "endpoints": {
            "exchanges": "/exchanges - List all available exchanges",
            "bybit": {
                "start": "/bybit/start - Start ByBit trading bot",
                "stop": "/bybit/stop - Stop ByBit trading bot",
                "status": "/bybit/status - Get ByBit bot status",
                "balance": "/bybit/balance - Get ByBit account balance",
                "stats": "/bybit/stats - Get ByBit trading statistics"
            },
            "binance": {
                "info": "/binance/* - Binance endpoints (coming soon)"
            },
            "cryptocom": {
                "info": "/cryptocom/* - Crypto.com endpoints (coming soon)"
            }
        }
    }


@app.get("/exchanges")
async def list_exchanges():
    """List all available exchanges and their status"""
    return {
        "exchanges": [
            {
                "id": name,
                "name": data["name"],
                "enabled": data["enabled"],
                "running": data["task"] is not None and not data["task"].done(),
                "has_instance": data["instance"] is not None,
                "is_started": data["is_started"]
            }
            for name, data in traders.items()
        ]
    }




# ==================== BYBIT ENDPOINTS ====================

@app.post("/bybit/start")
async def start_bybit_trading():
    """Start the ByBit trading bot"""
    global traders, main_loop
    
    if not traders["bybit"]["enabled"]:
        raise HTTPException(status_code=400, detail="ByBit module is not enabled")
    
    if traders["bybit"]["task"] and not traders["bybit"]["task"].done():
        raise HTTPException(status_code=400, detail="ByBit trading bot is already running")
    
    if main_loop is None:
        raise HTTPException(status_code=500, detail="Event loop not initialized")
    
    try:
        # Create ByBit trader instance
        trader_instance = ByBitSpotTrader(loop=main_loop, key=BYBIT_API_KEY, secret=BYBIT_SECRET_KEY)
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


@app.post("/bybit/stop")
async def stop_bybit_trading():
    """Stop the ByBit trading bot"""
    global traders
    
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


@app.get("/bybit/status")
async def get_bybit_status():
    """Get current ByBit trading bot status"""
    global traders
    
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


@app.get("/bybit/balance")
async def get_bybit_balance():
    """Get current ByBit account balance"""
    global traders
    
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


@app.get("/bybit/stats")
async def get_bybit_stats():
    """Get ByBit trading statistics"""
    global traders
    
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


# ==================== BINANCE ENDPOINTS (PLACEHOLDER) ====================

@app.get("/binance/info")
async def binance_info():
    """Binance module information"""
    return {
        "exchange": "binance",
        "status": "not_implemented",
        "message": "Binance trading module will be added soon",
        "enabled": traders["binance"]["enabled"]
    }


@app.post("/binance/start")
async def start_binance_trading():
    """Start Binance trading bot (not yet implemented)"""
    raise HTTPException(
        status_code=501,
        detail="Binance trading module is not yet implemented. Coming soon!"
    )


# ==================== CRYPTO.COM ENDPOINTS (PLACEHOLDER) ====================

@app.get("/cryptocom/info")
async def cryptocom_info():
    """Crypto.com module information"""
    return {
        "exchange": "cryptocom",
        "status": "not_implemented",
        "message": "Crypto.com trading module will be added soon",
        "enabled": traders["cryptocom"]["enabled"]
    }


@app.post("/cryptocom/start")
async def start_cryptocom_trading():
    """Start Crypto.com trading bot (not yet implemented)"""
    raise HTTPException(
        status_code=501,
        detail="Crypto.com trading module is not yet implemented. Coming soon!"
    )


# ==================== MAIN ====================

if __name__ == "__main__":
    # Run the FastAPI application with uvicorn
    uvicorn.run(
        "api_main:app",
        host="0.0.0.0",
        port=8000,
        reload=False,
        log_level="info"
    )
