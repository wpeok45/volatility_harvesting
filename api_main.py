import asyncio
from contextlib import asynccontextmanager
from fastapi import FastAPI, HTTPException
from fastapi.responses import JSONResponse
import uvicorn

# Import the Trader class from vh_float
from vh_float import Trader as ByBitSpotTrader, API_KEY, SECRET_KEY

# Global variables
trader_instance = None
trader_task = None
main_loop = None


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Manage the lifecycle of the trading bot"""
    global trader_instance, trader_task, main_loop
    
    print("Starting FastAPI application...")
    
    # Initialize event loop
    main_loop = asyncio.get_running_loop()
    
    yield
    
    # Cleanup on shutdown
    print("Shutting down FastAPI application...")
    if trader_task and not trader_task.done():
        trader_task.cancel()
        try:
            await trader_task
        except asyncio.CancelledError:
            print("Trading task cancelled successfully")


app = FastAPI(
    title="Volatility Harvesting Trading Bot",
    description="API for managing cryptocurrency volatility harvesting bot",
    version="1.0.0",
    lifespan=lifespan
)


@app.get("/")
async def root():
    """Root endpoint"""
    return {
        "message": "Volatility Harvesting Trading Bot API",
        "status": "running" if trader_task and not trader_task.done() else "stopped",
        "endpoints": {
            "start": "/start - Start trading bot",
            "stop": "/stop - Stop trading bot",
            "status": "/status - Get bot status",
            "balance": "/balance - Get account balance",
            "stats": "/stats - Get trading statistics"
        }
    }


@app.post("/start")
async def start_trading():
    """Start the trading bot"""
    global trader_instance, trader_task, main_loop
    
    if trader_task and not trader_task.done():
        raise HTTPException(status_code=400, detail="Trading bot is already running")
    
    try:
        # Create trader instance
        trader_instance = ByBitSpotTrader(loop=main_loop, key=API_KEY, secret=SECRET_KEY)
        
        # Initialize trader data
        await trader_instance.init_data()
        
        # Start websocket connections and trading tasks
        asyncio.create_task(trader_instance.ws_ticker())
        await asyncio.sleep(1.0)
        asyncio.create_task(trader_instance.ws_user_data())
        asyncio.create_task(trader_instance.account_balance_loop())
        asyncio.create_task(trader_instance.save_history_loop())
        
        # Start main trading loop
        trader_task = asyncio.create_task(trader_instance.trade_loop())
        
        return JSONResponse(
            status_code=200,
            content={
                "message": "Trading bot started successfully",
                "symbol": trader_instance.symbol,
                "status": "running"
            }
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to start trading bot: {str(e)}")


@app.post("/stop")
async def stop_trading():
    """Stop the trading bot"""
    global trader_task
    
    if not trader_task or trader_task.done():
        raise HTTPException(status_code=400, detail="Trading bot is not running")
    
    try:
        trader_task.cancel()
        await trader_task
    except asyncio.CancelledError:
        pass
    
    return JSONResponse(
        status_code=200,
        content={
            "message": "Trading bot stopped successfully",
            "status": "stopped"
        }
    )


@app.get("/status")
async def get_status():
    """Get current trading bot status"""
    global trader_instance, trader_task
    
    if not trader_instance:
        return {
            "status": "not_initialized",
            "message": "Trading bot has not been started yet"
        }
    
    is_running = trader_task and not trader_task.done()
    
    status_info = {
        "status": "running" if is_running else "stopped",
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


@app.get("/balance")
async def get_balance():
    """Get current account balance"""
    global trader_instance
    
    if not trader_instance:
        raise HTTPException(status_code=400, detail="Trading bot not initialized")
    
    await trader_instance.get_account_balance()
    
    return {
        "native_balance": {
            trader_instance.pair[0]: trader_instance.ta.native_balance[0],
            trader_instance.pair[1]: trader_instance.ta.native_balance[1]
        },
        "pair_balance": trader_instance.ta.pair_balance,
        "real_ratio": trader_instance.ta.real_ratio,
        "last_price": trader_instance.last_price
    }


@app.get("/stats")
async def get_stats():
    """Get trading statistics"""
    global trader_instance
    
    if not trader_instance:
        raise HTTPException(status_code=400, detail="Trading bot not initialized")
    
    return {
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


if __name__ == "__main__":
    # Run the FastAPI application with uvicorn
    uvicorn.run(
        "api_main:app",
        host="0.0.0.0",
        port=8000,
        reload=False,
        log_level="info"
    )
