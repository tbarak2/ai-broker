# AI Broker — REST API Reference

Base URL: `http://localhost:8000/api`

All responses are JSON. All timestamps are ISO 8601 UTC.

---

## Portfolio

### Create Portfolio
`POST /api/portfolio/`

**Request:**
```json
{
  "name": "My First Portfolio",
  "initial_capital": 10000.00
}
```

**Response `201`:**
```json
{
  "id": 1,
  "name": "My First Portfolio",
  "initial_capital": "10000.00",
  "cash_balance": "10000.00",
  "total_value": "10000.00",
  "total_pnl": "0.00",
  "total_pnl_pct": 0.0,
  "created_at": "2025-01-15T10:00:00Z"
}
```

---

### Get Portfolio Summary
`GET /api/portfolio/{id}/`

**Response `200`:**
```json
{
  "id": 1,
  "name": "My First Portfolio",
  "initial_capital": "10000.00",
  "cash_balance": "8450.00",
  "total_value": "12345.67",
  "total_pnl": "2345.67",
  "total_pnl_pct": 23.46,
  "positions_count": 3,
  "created_at": "2025-01-15T10:00:00Z",
  "updated_at": "2025-01-20T15:30:00Z"
}
```

---

### List Portfolios
`GET /api/portfolio/`

---

### Get Positions
`GET /api/portfolio/{id}/positions/`

**Response `200`:**
```json
[
  {
    "id": 1,
    "symbol": "AAPL",
    "asset_type": "STOCK",
    "quantity": "10.00",
    "avg_cost_price": "180.50",
    "current_price": "185.20",
    "market_value": "1852.00",
    "unrealized_pnl": "47.00",
    "unrealized_pnl_pct": 2.60,
    "realized_pnl": "0.00",
    "weight_pct": 15.00
  }
]
```

---

### Get P&L History (Chart Data)
`GET /api/portfolio/{id}/pnl/?period=30d`

Query params: `period` = `1d` | `7d` | `30d` | `90d` | `1y`

**Response `200`:**
```json
{
  "period": "30d",
  "data": [
    {"date": "2025-01-01", "total_value": 10000.00, "pnl": 0.00},
    {"date": "2025-01-02", "total_value": 10250.00, "pnl": 250.00}
  ]
}
```

---

### Get Portfolio Metrics
`GET /api/portfolio/{id}/metrics/`

**Response `200`:**
```json
{
  "sharpe_ratio": 1.42,
  "max_drawdown_pct": -8.30,
  "win_rate_pct": 62.5,
  "total_trades": 24,
  "profitable_trades": 15,
  "avg_trade_pnl": "48.20",
  "best_trade": {"symbol": "NVDA", "pnl": "420.00"},
  "worst_trade": {"symbol": "TSLA", "pnl": "-180.00"}
}
```

---

## Orders

### Create Manual Order
`POST /api/orders/`

**Request:**
```json
{
  "portfolio": 1,
  "symbol": "AAPL",
  "asset_type": "STOCK",
  "side": "BUY",
  "order_type": "MARKET",
  "quantity": 5
}
```

For LIMIT orders, include `"limit_price": 182.00`.
For STOP orders, include `"stop_price": 170.00`.

**Response `201`:**
```json
{
  "id": 42,
  "portfolio": 1,
  "symbol": "AAPL",
  "asset_type": "STOCK",
  "side": "BUY",
  "order_type": "MARKET",
  "quantity": "5.00",
  "status": "PENDING_APPROVAL",
  "source": "MANUAL",
  "created_at": "2025-01-20T15:30:00Z"
}
```

---

### List Orders
`GET /api/orders/?portfolio=1&status=EXECUTED&symbol=AAPL`

Query params:
- `portfolio` — filter by portfolio ID
- `status` — `PENDING_APPROVAL` | `APPROVED` | `REJECTED` | `EXECUTED` | `CANCELLED` | `FAILED`
- `symbol` — filter by ticker
- `side` — `BUY` | `SELL`
- `source` — `AI_SUGGESTED` | `MANUAL`

---

### Approve Order
`POST /api/orders/{id}/approve/`

No body required.

**Response `200`:**
```json
{"status": "APPROVED", "message": "Order #42 approved and queued for execution"}
```

---

### Cancel Order
`POST /api/orders/{id}/cancel/`

---

## AI Recommendations

### List Recommendations
`GET /api/recommendations/?portfolio=1&status=PENDING&provider=claude`

Query params:
- `portfolio` — filter by portfolio
- `status` — `PENDING` | `APPROVED` | `REJECTED` | `EXECUTED` | `EXPIRED`
- `provider` — `claude` | `openai` | `gemini`
- `action` — `BUY` | `SELL` | `HOLD` | `REBALANCE`
- `symbol` — filter by ticker

**Response `200`:**
```json
[
  {
    "id": 42,
    "provider": "claude",
    "symbol": "AAPL",
    "asset_type": "STOCK",
    "action": "BUY",
    "confidence": 0.78,
    "quantity_suggested": "5.00",
    "price_target": "195.00",
    "stop_loss": "175.00",
    "take_profit": "200.00",
    "reasoning": "RSI at 32 indicates oversold conditions. Positive earnings beat and strong Asia demand suggest recovery. Technical indicators align with fundamental strength.",
    "status": "PENDING",
    "created_at": "2025-01-20T15:00:00Z",
    "expires_at": "2025-01-21T15:00:00Z",
    "analysis_data": {
      "rsi": 32.1,
      "macd": -0.45,
      "sentiment_score": 0.65,
      "pe_ratio": 28.5
    }
  }
]
```

---

### Approve Recommendation
`POST /api/recommendations/{id}/approve/`

Creates an `Order` in `PENDING_APPROVAL` → immediately moves to `APPROVED`.

**Response `200`:**
```json
{
  "recommendation_id": 42,
  "order_id": 15,
  "status": "Order created and approved",
  "order": { ... }
}
```

---

### Reject Recommendation
`POST /api/recommendations/{id}/reject/`

**Request (optional):**
```json
{"reason": "Too risky given current market conditions"}
```

**Response `200`:**
```json
{"status": "REJECTED"}
```

---

## Market Data

### Get Current Quote
`GET /api/market/quote/{symbol}/`

**Response `200`:**
```json
{
  "symbol": "AAPL",
  "price": 185.20,
  "change": 2.30,
  "change_pct": 1.26,
  "volume": 48234567,
  "market_cap": 2850000000000,
  "timestamp": "2025-01-20T20:00:00Z",
  "source": "alpaca"
}
```

---

### Get Historical OHLCV
`GET /api/market/history/{symbol}/?period=90d&interval=1d`

Query params:
- `period` — `7d` | `30d` | `90d` | `1y`
- `interval` — `1h` | `1d` | `1w`

**Response `200`:**
```json
{
  "symbol": "AAPL",
  "period": "90d",
  "interval": "1d",
  "data": [
    {
      "date": "2024-10-15",
      "open": 182.10,
      "high": 186.30,
      "low": 181.50,
      "close": 185.20,
      "volume": 48234567
    }
  ]
}
```

---

### Get Technical Indicators
`GET /api/market/indicators/{symbol}/`

**Response `200`:**
```json
{
  "symbol": "AAPL",
  "timestamp": "2025-01-20T20:00:00Z",
  "rsi_14": 32.1,
  "macd": -0.45,
  "macd_signal": -0.20,
  "macd_histogram": -0.25,
  "bb_upper": 192.50,
  "bb_middle": 185.00,
  "bb_lower": 177.50,
  "ema_20": 184.30,
  "ema_50": 183.10,
  "ema_200": 175.80
}
```

---

## Trades

### List Trades
`GET /api/trades/?portfolio=1&symbol=AAPL`

**Response `200`:**
```json
[
  {
    "id": 1,
    "order_id": 42,
    "symbol": "AAPL",
    "side": "BUY",
    "quantity": "5.00",
    "price": "185.20",
    "total_cost": "926.00",
    "commission": "0.00",
    "portfolio_balance_after": "8524.00",
    "executed_at": "2025-01-20T15:35:00Z"
  }
]
```

---

## Settings

### Get Strategy Config
`GET /api/settings/strategy/?portfolio=1`

**Response `200`:**
```json
{
  "id": 1,
  "portfolio": 1,
  "ai_providers": ["claude", "openai", "gemini"],
  "strategies": ["technical", "sentiment", "fundamental", "rebalancing"],
  "risk_tolerance": "MEDIUM",
  "max_position_size_pct": "10.00",
  "analysis_interval_minutes": 30,
  "watchlist": ["AAPL", "MSFT", "NVDA", "TSLA", "BTC-USD", "SPY"]
}
```

---

### Update Strategy Config
`PUT /api/settings/strategy/{id}/`

**Request:**
```json
{
  "ai_providers": ["claude", "openai"],
  "risk_tolerance": "LOW",
  "max_position_size_pct": 5.0,
  "watchlist": ["AAPL", "MSFT", "GOOGL"]
}
```

---

## WebSocket Events (future)

Connect to `ws://localhost:8000/ws/portfolio/{id}/` for real-time updates.

| Event | Payload |
|-------|---------|
| `price_update` | `{"symbol": "AAPL", "price": 185.50}` |
| `recommendation_new` | Full recommendation object |
| `trade_executed` | Full trade object |
| `portfolio_updated` | Updated portfolio summary |

---

## Error Responses

All errors follow this structure:

```json
{
  "error": "insufficient_funds",
  "message": "Cash balance $450.00 is insufficient for this order (required: $926.00)",
  "detail": {}
}
```

Common HTTP status codes:
- `400` Bad Request — validation error
- `404` Not Found — resource does not exist
- `409` Conflict — e.g. approving an already-executed recommendation
- `422` Unprocessable Entity — business rule violation (insufficient funds)
- `500` Internal Server Error
