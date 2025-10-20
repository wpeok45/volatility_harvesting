"""
Multi-Exchange Volatility Harvesting Trading Bot API
Main application file
"""
import asyncio
from contextlib import asynccontextmanager
from fastapi import FastAPI
import uvicorn

# Import API modules
from api import bybit_router, binance_router, cryptocom_router
from api.dependencies import traders, set_main_loop
from api.config import save_api_config, load_api_config
from api.bybit import start_bybit_internal


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Manage the lifecycle of all trading bots"""
    
    print("Starting Multi-Exchange Volatility Harvesting API...")
    
    # Load saved configuration
    load_api_config()
    
    # Initialize event loop
    set_main_loop(asyncio.get_running_loop())
    
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
    description="API for managing cryptocurrency volatility harvesting across multiple exchanges.",
    version="2.0.0",
    lifespan=lifespan
)


# Include routers
app.include_router(bybit_router)
app.include_router(binance_router)
app.include_router(cryptocom_router)


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
