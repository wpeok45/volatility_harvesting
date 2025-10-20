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
├── models.py             # Pydantic models for requests/responses
├── auth.py               # OAuth2 authentication (Bearer token)
├── dependencies.py       # Shared dependencies (traders, main_loop, data dirs)
├── config.py             # Configuration management (save/load)
├── bybit.py              # Routes for ByBit exchange
├── binance.py            # Routes for Binance (placeholder)
└── cryptocom.py          # Routes for Crypto.com (placeholder)
```

## Files

### `models.py` 🆕
- **Authentication Models**: `Token`, `TokenData`, `User`
- **Main API Models**: `ExchangeStatus`, `RootResponse`, `ExchangeInfo`, `ExchangesResponse`
- **Trading Bot Models**: `StartResponse`, `StopResponse`, `StatusResponse`, `BalanceInfo`, `BalanceResponse`, `StatsResponse`
- All models include field examples for automatic documentation
- Centralized location for all Pydantic models

### `auth.py` 🆕
- OAuth2 password flow with JWT tokens
- `authenticate_user()` - validate credentials from `.env`
- `create_access_token()` - generate JWT tokens
- `get_current_user()` - dependency for protected endpoints
- Token expiration: 30 minutes (configurable)

### `dependencies.py`
- Global variables: `traders`, `main_loop`
- Data directories: `EXCHANGE_DATA_DIRS`
- Automatic creation of folders for each exchange
- Functions: `get_main_loop()`, `set_main_loop()`

### `config.py`
- `save_api_config()` - save settings to JSON
- `load_api_config()` - load settings from JSON

### `bybit.py`
- `POST /bybit/start` - start trading bot (🔒 requires auth)
- `POST /bybit/stop` - stop trading bot (🔒 requires auth)
- `GET /bybit/status` - get bot status (🔒 requires auth)
- `GET /bybit/balance` - get account balance (🔒 requires auth)
- `GET /bybit/stats` - get trading statistics (🔒 requires auth)
- `start_bybit_internal()` - internal function for auto-start
- Complete response models with examples

### `binance.py` & `cryptocom.py`
- Placeholder endpoints (501 Not Implemented)
- Authentication required (🔒)
- Ready for module implementation

## Usage

### Authentication

All endpoints except `/` (root) and `/token` require OAuth2 authentication:

1. **Get Access Token:**
   ```bash
   curl -X POST http://localhost:8000/token \
     -d "username=admin&password=yourpassword"
   ```

   Response:
   ```json
   {
     "access_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
     "token_type": "bearer"
   }
   ```

2. **Use Token in Requests:**
   ```bash
   curl -H "Authorization: Bearer YOUR_TOKEN" \
     http://localhost:8000/bybit/status
   ```

### Interactive Documentation

Visit http://localhost:8000/docs to use the interactive Swagger UI:
- Click "Authorize" button (🔒 icon)
- Enter username and password
- All subsequent requests will include the token automatically

### Response Models

All endpoints return structured JSON responses with proper OpenAPI schemas:
- **Request samples**: Auto-generated from endpoint parameters
- **Response samples**: Defined with Pydantic models and examples
- **Error responses**: Documented with status codes (400, 401, 500, etc.)

### Code Example

```python
from api import bybit_router, binance_router, cryptocom_router

app = FastAPI()
app.include_router(bybit_router)
app.include_router(binance_router)
app.include_router(cryptocom_router)
```

## Adding a New Exchange

1. **Create file** `api/exchange_name.py`:
   ```python
   from fastapi import APIRouter, HTTPException, Depends
   from .dependencies import traders, get_main_loop, EXCHANGE_DATA_DIRS
   from .config import save_api_config
   from .auth import get_current_user
   from .models import User, StartResponse, StopResponse, StatusResponse

   router = APIRouter(prefix="/exchange", tags=["Exchange"])

   @router.post("/start", response_model=StartResponse)
   async def start_exchange_trading(current_user: User = Depends(get_current_user)):
       """Start trading bot (requires authentication)"""
       # Implementation here
       return {"message": "Started", "exchange": "exchange", "status": "running", "is_started": True}
   ```

2. **Define models** (if needed) in `api/models.py`:
   ```python
   class ExchangeCustomResponse(BaseModel):
       """Custom response for specific exchange"""
       field: str = Field(default=..., examples=["value"])
   ```

3. **Import in** `api/__init__.py`:
   ```python
   from .exchange_name import router as exchange_router
   ```

4. **Include in** `api_main.py`:
   ```python
   from api import bybit_router, binance_router, cryptocom_router, exchange_router
   app.include_router(exchange_router)
   ```

5. **Add to traders dict** in `api/dependencies.py`:
   ```python
   traders = {
       "exchange": {
           "instance": None,
           "task": None,
           "tasks": [],
           "enabled": True,
           "name": "Exchange Name",
           "is_started": False
       }
   }
   ```

6. **Create data directory** in `EXCHANGE_DATA_DIRS`:
   ```python
   EXCHANGE_DATA_DIRS = {
       "exchange": Path("data/exchange")
   }
   ```

## Advantages of Modular Structure

- ✅ Clean and organized code
- ✅ Easy to add new exchanges
- ✅ Isolation of each exchange logic
- ✅ Simple testing of individual modules
- ✅ Code reusability through dependencies
- ✅ Automatic documentation with tags
- ✅ Independent data storage per exchange
- ✅ Centralized authentication
- ✅ Type-safe with Pydantic models
- ✅ Complete API documentation with examples
