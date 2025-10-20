#!/bin/bash

# Multi-Exchange Volatility Harvesting API - Quick Examples
# =========================================================

BASE_URL="http://localhost:8000"

echo "🚀 Multi-Exchange Volatility Harvesting API Examples"
echo "====================================================="
echo ""

# ==================== General Endpoints ====================
echo "📋 1. Get API Overview"
curl -s $BASE_URL/ | jq .
echo ""

echo "📋 2. List All Exchanges"
curl -s $BASE_URL/exchanges | jq .
echo ""

# ==================== ByBit Endpoints ====================
echo "🟢 ByBit Section"
echo "==============="
echo ""

echo "▶️  3. Start ByBit Trading Bot"
curl -X POST $BASE_URL/bybit/start | jq .
echo ""

sleep 2

echo "📊 4. Get ByBit Status"
curl -s $BASE_URL/bybit/status | jq .
echo ""

echo "💰 5. Get ByBit Balance"
curl -s $BASE_URL/bybit/balance | jq .
echo ""

echo "📈 6. Get ByBit Statistics"
curl -s $BASE_URL/bybit/stats | jq .
echo ""

# Uncomment to stop the bot
# echo "⏹️  7. Stop ByBit Trading Bot"
# curl -X POST $BASE_URL/bybit/stop | jq .
# echo ""

# ==================== Binance Endpoints (Placeholder) ====================
echo "🟡 Binance Section (Coming Soon)"
echo "================================"
echo ""

echo "ℹ️  8. Get Binance Info"
curl -s $BASE_URL/binance/info | jq .
echo ""

# This will return 501 Not Implemented
echo "▶️  9. Try to Start Binance Bot (Not Yet Implemented)"
curl -X POST $BASE_URL/binance/start 2>/dev/null || echo "Expected: 501 Not Implemented"
echo ""

# ==================== Crypto.com Endpoints (Placeholder) ====================
echo "🔵 Crypto.com Section (Coming Soon)"
echo "==================================="
echo ""

echo "ℹ️  10. Get Crypto.com Info"
curl -s $BASE_URL/cryptocom/info | jq .
echo ""

# This will return 501 Not Implemented
echo "▶️  11. Try to Start Crypto.com Bot (Not Yet Implemented)"
curl -X POST $BASE_URL/cryptocom/start 2>/dev/null || echo "Expected: 501 Not Implemented"
echo ""

echo "✅ Examples completed!"
echo ""
echo "💡 Tips:"
echo "  - Visit $BASE_URL/docs for interactive Swagger UI"
echo "  - Visit $BASE_URL/redoc for alternative documentation"
echo "  - Check trading.log for detailed bot activity"
