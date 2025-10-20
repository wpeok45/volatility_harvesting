# Multi-Exchange Volatility Harvesting API

API for managing trading bots across multiple exchanges with modular architecture.

## 🏗️ Architecture

The API is built with a modular structure where each exchange has its own section of endpoints:
- **ByBit** - fully implemented (vh_float.py)
- **Binance** - ready to connect (placeholder endpoints)
- **Crypto.com** - ready to connect (placeholder endpoints)

## 📡 Endpoints

### General Endpoints

#### `GET /`
Root page with information about all available exchanges and endpoints

**Response:**
```json
{
  "message": "Multi-Exchange Volatility Harvesting Trading Bot API",
  "version": "2.0.0",
  "exchanges": {
    "bybit": {
      "enabled": true,
      "status": "stopped",
      "name": "ByBit Spot"
    },
    "binance": {...},
    "cryptocom": {...}
  },
  "endpoints": {...}
}
```

#### `GET /exchanges`
List of all available exchanges and their statuses

**Response:**
```json
{
  "exchanges": [
    {
      "id": "bybit",
      "name": "ByBit Spot",
      "enabled": true,
      "running": false,
      "has_instance": false
    },
    ...
  ]
}
```

---

### ByBit Endpoints

#### `POST /bybit/start`
Start ByBit trading bot

**Response:**
```json
{
  "exchange": "bybit",
  "message": "ByBit trading bot started successfully",
  "symbol": "BTCUSDC",
  "status": "running"
}
```

**Errors:**
- `400` - Bot is already running
- `500` - Error starting bot

#### `POST /bybit/stop`
Stop ByBit trading bot

**Response:**
```json
{
  "exchange": "bybit",
  "message": "ByBit trading bot stopped successfully",
  "status": "stopped"
}
```

#### `GET /bybit/status`
Get current ByBit bot status

**Response:**
```json
{
  "exchange": "bybit",
  "status": "running",
  "symbol": "BTCUSDC",
  "last_price": 67800.5,
  "portfolio_ratio": 50.0,
  "real_ratio": 48.5,
  "ATH": 73000.0,
  "work_range": 36500.0,
  "local_range": 450,
  "ma_trend": 67750.0,
  "ma_fast": 67820.0
}
```

#### `GET /bybit/balance`
Get ByBit account balance

**Response:**
```json
{
  "exchange": "bybit",
  "native_balance": {
    "BTC": 0.15,
    "USDC": 10200.50
  },
  "pair_balance": {
    "BTC": 10170.075,
    "USDC": 10200.50
  },
  "real_ratio": 49.93,
  "last_price": 67800.5
}
```

#### `GET /bybit/stats`
Get detailed ByBit trading statistics

**Response:**
```json
{
  "exchange": "bybit",
  "symbol": "BTCUSDC",
  "last_price": 67800.5,
  "traded_price": 67750.0,
  "buy_price_mean": 67500.0,
  "trade_profit": 45.08,
  "percent_diff": 0.22,
  "price_diff": 50.5,
  "portfolio_ratio": 50.0,
  "real_ratio": 49.93,
  "ATH": 73000.0,
  "work_range": 36500.0,
  "local_range": 450,
  "rebalance_top": 3.0,
  "rebalance_bottom": 3.0,
  "min_profitable_percent": 0.65,
  "order_scale": {
    "enabled": false,
    "buy_counter": 1,
    "sell_counter": 1,
    "buy_percent": 3.0,
    "sell_percent": 3.0
  },
  "impuls": 5,
  "impuls_percent": 2.5,
  "impuls_harmonic": 12.5,
  "impuls_harmonic_percent": 3.2,
  "ma_trend": 67750.0,
  "ma_fast": 67820.0
}
```

---

### Binance Endpoints (Coming Soon)

#### `GET /binance/info`
Binance module information

**Response:**
```json
{
  "exchange": "binance",
  "status": "not_implemented",
  "message": "Binance trading module will be added soon",
  "enabled": false
}
```

#### `POST /binance/start`
**Response:** `501 Not Implemented`

---

### Crypto.com Endpoints (Coming Soon)

#### `GET /cryptocom/info`
Crypto.com module information

**Response:**
```json
{
  "exchange": "cryptocom",
  "status": "not_implemented",
  "message": "Crypto.com trading module will be added soon",
  "enabled": false
}
```

#### `POST /cryptocom/start`
**Response:** `501 Not Implemented`

---

## 🚀 Running

### Install Dependencies
```bash
pip install -r requirements.txt
```

### Start Server
```bash
# Method 1: Via Python
python api_main.py

# Method 2: Via uvicorn
uvicorn api_main:app --host 0.0.0.0 --port 8000

# Method 3: With auto-reload for development
uvicorn api_main:app --host 0.0.0.0 --port 8000 --reload
```

### Access API
- **API**: http://localhost:8000
- **Swagger UI (documentation)**: http://localhost:8000/docs
- **ReDoc (alternative documentation)**: http://localhost:8000/redoc

---

## 📝 Usage Examples

### cURL

```bash
# List exchanges
curl http://localhost:8000/exchanges

# Start ByBit bot
curl -X POST http://localhost:8000/bybit/start

# ByBit status
curl http://localhost:8000/bybit/status

# ByBit balance
curl http://localhost:8000/bybit/balance

# ByBit statistics
curl http://localhost:8000/bybit/stats

# Stop ByBit bot
curl -X POST http://localhost:8000/bybit/stop
```

### Python (requests)

```python
import requests

BASE_URL = "http://localhost:8000"

# Start bot
response = requests.post(f"{BASE_URL}/bybit/start")
print(response.json())

# Get status
response = requests.get(f"{BASE_URL}/bybit/status")
print(response.json())

# Stop bot
response = requests.post(f"{BASE_URL}/bybit/stop")
print(response.json())
```

### JavaScript (fetch)

```javascript
const BASE_URL = "http://localhost:8000";

// Start bot
fetch(`${BASE_URL}/bybit/start`, { method: "POST" })
  .then(res => res.json())
  .then(data => console.log(data));

// Get status
fetch(`${BASE_URL}/bybit/status`)
  .then(res => res.json())
  .then(data => console.log(data));
```

---

## 🔧 Adding a New Exchange

### Step 1: Create Trader Module
Create a file `binance_trader.py` (or `cryptocom_trader.py`) with a `Trader` class, similar to `vh_float.py`:

```python
class Trader:
    def __init__(self, loop, key, secret):
        self.loop = loop
        self.key = key
        self.secret = secret
        # ... остальная инициализация
    
    async def init_data(self):
        # Initialize data
        pass
    
    async def trade_loop(self):
        # Main trading loop
        pass
    
    # ... other methods
```

### Step 2: Import in api_main.py
Uncomment and configure the import at the beginning of `api_main.py`:

```python
from binance_trader import Trader as BinanceSpotTrader, API_KEY as BINANCE_API_KEY, SECRET_KEY as BINANCE_SECRET_KEY
```

### Step 3: Enable Exchange
Change `enabled: False` to `True` in the `traders` dictionary:

```python
traders = {
    "binance": {
        "instance": None,
        "task": None,
        "enabled": True,  # Change to True
        "name": "Binance Spot"
    },
}
```

### Step 4: Implement Endpoints
Copy and adapt ByBit endpoints for the new exchange:

```python
@app.post("/binance/start")
async def start_binance_trading():
    # Similar to start_bybit_trading()
    pass
```

---

## 🏗️ Project Structure

```
/projects/volatility_harvesting/
├── api_main.py              # FastAPI application (multi-exchange)
├── vh_float.py              # ByBit trader
├── binance_vh_float.py        # Binance trader (TODO)
├── cryptocom_vh_float.py      # Crypto.com trader (TODO)
├── requirements.txt         # Python dependencies
├── .env                     # Environment variables (API keys)
└── API_STRUCTURE.md         # This file
```

---

## 🔐 Environment Variables Setup

Create `.env` file for each exchange:

```env
# ByBit
API_KEY=your_bybit_api_key
SECRET_KEY=your_bybit_secret_key
STABLE_PAIR=USDT

# Binance (TODO)
BINANCE_API_KEY=your_binance_api_key
BINANCE_SECRET_KEY=your_binance_secret_key
BINANCE_STABLE_PAIR=USDT

# Crypto.com (TODO)
CRYPTOCOM_API_KEY=your_cryptocom_api_key
CRYPTOCOM_SECRET_KEY=your_cryptocom_secret_key
CRYPTOCOM_STABLE_PAIR=USDT

# Common settings
MA_LENGTH=24.0
RANGE=50.0
# ... other parameters
```

---

## 📊 Monitoring

API provides detailed information for monitoring:
- Current price and trends
- Portfolio balance
- Profit/Loss
- Rebalancing parameters
- Dynamic order status
- Technical indicators (MA, EMA)

Integrate with:
- Grafana + Prometheus
- Custom dashboards
- Telegram notifications (already built into vh_float.py)

---

## ⚠️ Important Notes

1. **Security**: Never commit API keys to Git
2. **Rate Limits**: Consider exchange API rate limits
3. **Testing**: Test on testnet before production
4. **Logging**: All operations are logged to `trading.log`
5. **Lifecycle**: API properly shuts down all bots on stop

---

## 📚 Dependencies

- `fastapi[standard]>=0.115.0` - Web framework
- `uvicorn[standard]>=0.32.0` - ASGI server
- `aiohttp>=3.12.14` - Async HTTP client
- `aiodns>=3.2.0` - DNS resolver
- `python-dotenv` - Environment variables

---

## 🤝 Contributing

When adding a new exchange:
1. Follow the structure of `vh_float.py`
2. Document all endpoints
3. Add usage examples
4. Test all scenarios

---

## 📄 License

See LICENSE file in the project root
