# API Module Structure

Modular API structure using FastAPI Router for each exchange.

## ⚠️ Security Warning

**CORS Configuration**: The API has **unrestricted CORS** enabled (`allow_origins=["*"]`). This means:
- ✅ Any web application can access the API from any domain
- ✅ Useful for development and testing
- ⚠️ **NOT recommended for production** without proper authentication
- ⚠️ Consider restricting `allow_origins` to specific domains in production
- 🔒 **Always use authentication tokens** when exposing to the internet

To restrict CORS in production, modify `api_main.py`:
```python
app.add_middleware(
    CORSMiddleware,
    allow_origins=["https://yourdomain.com"],  # Specific domains only
    allow_credentials=True,
    allow_methods=["GET", "POST"],  # Limit methods
    allow_headers=["*"],
)
```

## Structure

```
api/
├── __init__.py           # Export all routers
├── dependencies.py       # Shared dependencies (traders, main_loop, data dirs)
├── config.py            # Configuration management (save/load)
├── bybit.py             # Routes for ByBit exchange
├── binance.py           # Routes for Binance (placeholder)
└── cryptocom.py         # Routes for Crypto.com (placeholder)
```

## Files

### `dependencies.py`
- Global variables: `traders`, `main_loop`
- Data directories: `EXCHANGE_DATA_DIRS`
- Automatic creation of folders for each exchange
- Functions: `get_main_loop()`, `set_main_loop()`

### `config.py`
- `save_api_config()` - save settings to JSON
- `load_api_config()` - load settings from JSON

### `bybit.py`
- `POST /bybit/start` - start trading bot
- `POST /bybit/stop` - stop trading bot
- `GET /bybit/status` - get bot status
- `GET /bybit/balance` - get account balance
- `GET /bybit/stats` - get trading statistics
- `start_bybit_internal()` - internal function for auto-start

### `binance.py` & `cryptocom.py`
- Placeholder endpoints (501 Not Implemented)
- Ready for module implementation

## Usage

```python
from api import bybit_router, binance_router, cryptocom_router

app = FastAPI()
app.include_router(bybit_router)
app.include_router(binance_router)
app.include_router(cryptocom_router)
```

## Adding a New Exchange

1. Create file `api/exchange_name.py`
2. Import dependencies:
   ```python
   from fastapi import APIRouter
   from .dependencies import traders, get_main_loop, EXCHANGE_DATA_DIRS
   from .config import save_api_config
   ```
3. Create router:
   ```python
   router = APIRouter(prefix="/exchange", tags=["Exchange"])
   ```
4. Add endpoints (start, stop, status, etc.)
5. Import in `api/__init__.py`:
   ```python
   from .exchange_name import router as exchange_router
   ```
6. Include in `api_main.py`:
   ```python
   app.include_router(exchange_router)
   ```

## Advantages of Modular Structure

✅ Clean and organized code  
✅ Easy to add new exchanges  
✅ Isolation of each exchange logic  
✅ Simple testing of individual modules  
✅ Code reusability through dependencies  
✅ Automatic documentation with tags  
✅ Independent data storage per exchange
