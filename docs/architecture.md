# AI Broker — System Architecture

## Overview

AI Broker is a paper-trading simulator that uses multiple AI models (Claude, OpenAI, Gemini) to suggest stock trades. It manages a virtual portfolio, fetches real market data, and sends notifications and accepts commands via Telegram. The system is architected to be broker-agnostic — swapping from paper trading to a real broker (e.g. Alpaca) requires only a configuration change.

---

## System Diagram

```
┌─────────────────────────────────────────────────────────┐
│                    React Frontend                        │
│  Dashboard │ Portfolio │ Trades │ AI Suggestions │ Logs  │
└───────────────────────┬─────────────────────────────────┘
                        │ REST API + WebSocket
┌───────────────────────▼─────────────────────────────────┐
│                  Django DRF Backend                      │
│                                                          │
│  ┌──────────────┐  ┌──────────────┐  ┌───────────────┐  │
│  │ Portfolio    │  │ AI Advisor   │  │ Market Data   │  │
│  │ Service      │  │ Service      │  │ Service       │  │
│  └──────────────┘  └──────────────┘  └───────────────┘  │
│  ┌──────────────┐  ┌──────────────┐  ┌───────────────┐  │
│  │ Trade        │  │ Telegram     │  │ Analytics     │  │
│  │ Executor     │  │ Service      │  │ Service       │  │
│  └──────────────┘  └──────────────┘  └───────────────┘  │
│                                                          │
│  ┌───────────────────────────────────────────────────┐  │
│  │              Celery Task Queue                    │  │
│  │  fetch_prices │ run_analysis │ daily_report       │  │
│  │  check_stops  │ execute_approved_trades           │  │
│  └───────────────────────────────────────────────────┘  │
└─────────────────────────────────────────────────────────┘
         │                              │
┌────────▼──────────┐       ┌──────────▼──────────┐
│  PostgreSQL 16    │       │  Redis 7             │
│  (persistent DB)  │       │  (queue + cache)     │
└───────────────────┘       └─────────────────────┘
         │
┌────────▼──────────────────────────────────────────┐
│            External Services                       │
│  Alpaca API │ yfinance │ Claude │ OpenAI │ Gemini  │
│  Telegram Bot API │ Alpha Vantage (news)           │
└────────────────────────────────────────────────────┘
```

---

## Project Structure

```
ai_broker/
├── docker-compose.yml          # All services
├── .env.example                # Environment variable template
├── docs/
│   ├── architecture.md         # This file
│   ├── api.md                  # REST API reference
│   └── setup.md                # Local setup guide
│
├── backend/
│   ├── Dockerfile
│   ├── manage.py
│   ├── requirements.txt
│   ├── config/
│   │   ├── settings/
│   │   │   ├── base.py         # Shared settings
│   │   │   ├── local.py        # Dev overrides
│   │   │   └── production.py   # Prod overrides
│   │   ├── urls.py
│   │   ├── celery.py           # Celery app + Beat schedule
│   │   └── wsgi.py
│   │
│   ├── apps/
│   │   ├── portfolio/          # Portfolio, Position models + APIs
│   │   │   ├── models.py
│   │   │   ├── serializers.py
│   │   │   ├── views.py
│   │   │   ├── services.py     # PortfolioService (Facade)
│   │   │   ├── repositories.py # PortfolioRepository (Repository)
│   │   │   └── urls.py
│   │   │
│   │   ├── trading/            # Order, Trade models + APIs
│   │   │   ├── models.py
│   │   │   ├── serializers.py
│   │   │   ├── views.py
│   │   │   ├── services.py     # TradeExecutionService
│   │   │   ├── repositories.py
│   │   │   └── urls.py
│   │   │
│   │   ├── market_data/        # Price fetching, caching
│   │   │   ├── models.py       # PriceSnapshot, NewsItem
│   │   │   ├── serializers.py
│   │   │   ├── views.py
│   │   │   ├── services.py     # MarketDataService
│   │   │   ├── tasks.py        # Celery tasks
│   │   │   └── urls.py
│   │   │
│   │   ├── ai_advisor/         # Multi-model AI analysis
│   │   │   ├── models.py       # AIRecommendation, StrategyConfig
│   │   │   ├── serializers.py
│   │   │   ├── views.py
│   │   │   ├── services.py     # AIAdvisorService
│   │   │   ├── tasks.py        # run_ai_analysis Celery task
│   │   │   └── urls.py
│   │   │
│   │   ├── telegram_bot/       # Bot + notifications
│   │   │   ├── bot.py          # python-telegram-bot setup
│   │   │   ├── handlers.py     # Command handlers
│   │   │   ├── services.py     # TelegramNotificationService
│   │   │   └── tasks.py        # daily_report task
│   │   │
│   │   └── analytics/          # Reports, metrics
│   │       ├── services.py     # P&L, Sharpe ratio, drawdown
│   │       ├── views.py
│   │       └── urls.py
│   │
│   └── core/                   # Abstractions (no Django models here)
│       ├── brokers/
│       │   ├── base.py         # BaseBroker (ABC)
│       │   ├── paper.py        # PaperBroker
│       │   └── alpaca.py       # AlpacaBroker (future)
│       │
│       ├── data_providers/
│       │   ├── base.py         # BaseDataProvider (ABC)
│       │   ├── alpaca_provider.py   # Live prices
│       │   ├── yfinance_provider.py # Historical data
│       │   └── factory.py
│       │
│       ├── ai_providers/
│       │   ├── base.py         # BaseAIProvider (ABC) + AnalysisContext
│       │   ├── claude_provider.py
│       │   ├── openai_provider.py
│       │   ├── gemini_provider.py
│       │   └── factory.py      # AIProviderFactory
│       │
│       └── events/
│           └── signals.py      # Django signals for events
│
└── frontend/
    ├── Dockerfile
    ├── package.json
    ├── vite.config.ts
    └── src/
        ├── pages/
        │   ├── Dashboard/       # Portfolio value chart, P&L, activity
        │   ├── Portfolio/       # Positions table, allocation pie
        │   ├── AIAdvisor/       # Recommendation cards, approve/reject
        │   ├── Trades/          # Trade history table
        │   └── Settings/        # Watchlist, AI config, risk params
        ├── components/          # Shared UI components
        ├── hooks/               # TanStack Query data hooks
        ├── services/            # Axios API client
        └── store/               # Zustand global state
```

---

## Design Patterns

### 1. Strategy Pattern — AI Providers & Data Sources

All AI providers and data sources implement a common interface. The system selects the right implementation at runtime from configuration.

```python
# core/ai_providers/base.py
class BaseAIProvider(ABC):
    @abstractmethod
    def analyze(self, context: AnalysisContext) -> RecommendationData: ...

# Concrete strategies:
class ClaudeProvider(BaseAIProvider): ...
class OpenAIProvider(BaseAIProvider): ...
class GeminiProvider(BaseAIProvider): ...

# factory.py selects based on settings
provider = AIProviderFactory.create("claude")
result = provider.analyze(context)
```

The same pattern applies to `BaseDataProvider` → `AlpacaProvider` / `YFinanceProvider`.

### 2. Adapter Pattern — Broker Interface

The broker interface is identical for paper and real trading. Only the implementation changes.

```python
# core/brokers/base.py
class BaseBroker(ABC):
    @abstractmethod
    def place_order(self, order: Order) -> TradeResult: ...
    @abstractmethod
    def get_account_balance(self) -> Decimal: ...
    @abstractmethod
    def get_position(self, symbol: str) -> Optional[PositionData]: ...

class PaperBroker(BaseBroker):
    """Pure DB operations, no external calls"""

class AlpacaBroker(BaseBroker):  # future
    """Calls Alpaca REST API with real money"""
```

To go live: change `BROKER_BACKEND=paper` → `BROKER_BACKEND=alpaca` in `.env`.

### 3. Repository Pattern — Data Access

Business logic never touches the ORM directly. All queries go through repositories.

```python
# apps/portfolio/repositories.py
class PortfolioRepository:
    def get_by_id(self, portfolio_id: int) -> Portfolio: ...
    def get_positions(self, portfolio_id: int) -> QuerySet[Position]: ...
    def update_cash_balance(self, portfolio_id: int, amount: Decimal): ...
```

### 4. Facade Pattern — PortfolioService

A single service entry point hides the complexity of repositories + broker.

```python
# apps/portfolio/services.py
class PortfolioService:
    def __init__(self, repo: PortfolioRepository, broker: BaseBroker): ...
    def get_summary(self, portfolio_id: int) -> dict: ...
    def execute_trade(self, order: Order) -> Trade: ...
    def get_total_value(self, portfolio_id: int) -> Decimal: ...
```

### 5. Command Pattern — Orders

Orders are first-class objects that can be queued, approved, rejected, and replayed.

```
Order (created) → PENDING_APPROVAL
  → User approves (UI or Telegram /approve_N)
  → APPROVED
  → Celery task picks it up
  → EXECUTED (Trade record created)
  → Portfolio + Position updated
```

### 6. Observer Pattern — Django Signals

Events are published via Django signals. Subscribers (Telegram notifier, analytics updater) react independently.

```python
# core/events/signals.py
recommendation_created = Signal()
trade_executed = Signal()
stop_loss_triggered = Signal()

# telegram_bot/services.py
@receiver(recommendation_created)
def notify_recommendation(sender, recommendation, **kwargs):
    TelegramService.send_recommendation(recommendation)
```

---

## Data Models

### Portfolio App

| Model | Key Fields |
|-------|-----------|
| `Portfolio` | `name`, `initial_capital`, `cash_balance`, `user` |
| `Position` | `portfolio`, `symbol`, `asset_type`, `quantity`, `avg_cost_price`, `current_price`, `realized_pnl` |

`Position.unrealized_pnl` is a `@property` computed as `(current_price - avg_cost_price) * quantity`.

### Trading App

| Model | Key Fields |
|-------|-----------|
| `Order` | `portfolio`, `symbol`, `side` (BUY/SELL), `order_type`, `quantity`, `status`, `source` (AI/MANUAL), `ai_recommendation` |
| `Trade` | `order` (OneToOne), `symbol`, `side`, `quantity`, `price`, `commission`, `portfolio_balance_after` |

Order statuses: `PENDING_APPROVAL → APPROVED → EXECUTED` or `REJECTED / CANCELLED / FAILED`.

### AI Advisor App

| Model | Key Fields |
|-------|-----------|
| `AIRecommendation` | `portfolio`, `provider`, `symbol`, `action`, `confidence`, `quantity_suggested`, `price_target`, `stop_loss`, `take_profit`, `reasoning`, `analysis_data`, `status`, `expires_at` |
| `StrategyConfig` | `portfolio`, `ai_providers`, `strategies`, `risk_tolerance`, `max_position_size_pct`, `analysis_interval_minutes`, `watchlist` |

### Market Data App

| Model | Key Fields |
|-------|-----------|
| `PriceSnapshot` | `symbol`, `asset_type`, `open`, `high`, `low`, `close`, `volume`, `timestamp`, `source` |
| `NewsItem` | `symbol`, `headline`, `summary`, `source_url`, `sentiment_score`, `published_at` |

---

## AI Analysis Flow

```
Celery Beat (every 30 min)
        │
        ▼
run_ai_analysis_task(portfolio_id)
        │
        ├─► Fetch live prices (AlpacaProvider → Redis cache)
        ├─► Fetch 90-day OHLCV (yfinance)
        ├─► Compute indicators:
        │     RSI(14), MACD(12,26,9), Bollinger Bands(20), EMA(20,50,200)
        ├─► Fetch fundamentals from yfinance:
        │     P/E ratio, EPS, market cap, dividend yield
        ├─► Fetch recent news (Alpha Vantage)
        │     → Sentiment scoring per symbol
        │
        ▼
  Build AnalysisContext (serializable dict)
        │
        ├─► ClaudeProvider.analyze(context) ──► AIRecommendation (CLAUDE)
        ├─► OpenAIProvider.analyze(context) ──► AIRecommendation (OPENAI)
        └─► GeminiProvider.analyze(context) ──► AIRecommendation (GEMINI)
                │
                ▼
         recommendation_created signal fired
                │
                ▼
         Telegram notification:
         "📊 [CLAUDE] BUY AAPL — 5 shares @ ~$185
          Confidence: 78% | RSI oversold, positive earnings beat
          /approve_42  or  /reject_42"
```

### AI Prompt Structure

The prompt sent to each AI model contains:

```
You are an expert stock analyst and portfolio manager.

PORTFOLIO STATE:
- Cash available: $8,450.00
- Total value: $12,345.00
- Risk tolerance: MEDIUM
- Max position size: 10% of portfolio

ANALYSIS FOR: AAPL (US Stock)
Current price: $185.20

TECHNICAL INDICATORS:
- RSI(14): 32.1 (oversold)
- MACD: -0.45 (bearish momentum)
- Price vs EMA200: -3.2% (below long-term average)
- Bollinger: price near lower band

FUNDAMENTALS:
- P/E: 28.5 | EPS: $6.52 | Market Cap: $2.85T

NEWS SENTIMENT (last 24h): POSITIVE (0.65)
- "Apple beats Q1 earnings expectations" (+0.8)
- "iPhone demand strong in Asia" (+0.7)

CURRENT POSITIONS: [none]

Respond ONLY with valid JSON matching this schema:
{
  "action": "BUY" | "SELL" | "HOLD" | "REBALANCE",
  "confidence": 0.0-1.0,
  "quantity_suggested": <number>,
  "price_target": <number or null>,
  "stop_loss": <number or null>,
  "take_profit": <number or null>,
  "reasoning": "<1-3 sentence explanation>"
}
```

---

## Celery Task Schedule

| Task | Schedule | Description |
|------|----------|-------------|
| `fetch_market_prices` | Every 5 min (market hours) | Fetch latest prices, update Redis cache |
| `run_ai_analysis` | Every 30 min | Full AI analysis for all portfolios |
| `check_stop_loss_take_profit` | Every 5 min | Auto-create SELL orders when thresholds hit |
| `send_daily_report` | 18:00 EST daily | Telegram digest: P&L, top movers |
| `expire_old_recommendations` | Hourly | Mark stale recommendations as EXPIRED |
| `execute_approved_orders` | Every 1 min | Execute orders in APPROVED status |

---

## Tech Stack

| Layer | Technology | Version |
|-------|-----------|---------|
| Backend framework | Django + Django REST Framework | 5.x / 3.x |
| Async tasks | Celery + Celery Beat | 5.x |
| Message broker / cache | Redis | 7 |
| Database | PostgreSQL | 16 |
| Frontend framework | React + TypeScript + Vite | 18 / 5.x |
| UI components | Tailwind CSS + shadcn/ui | 3.x |
| Charts | Recharts | 2.x |
| Server state | TanStack Query | 5.x |
| Client state | Zustand | 4.x |
| HTTP client | Axios | latest |
| AI: Claude | `anthropic` Python SDK | latest |
| AI: OpenAI | `openai` Python SDK | latest |
| AI: Gemini | `google-generativeai` Python SDK | latest |
| Market data (live) | `alpaca-trade-api-v2` | latest |
| Market data (historical) | `yfinance` | latest |
| Technical analysis | `ta` (TA-Lib wrapper) | latest |
| Telegram | `python-telegram-bot` | v21 |
| Containerization | Docker + Docker Compose | v2 |
| Testing (backend) | pytest-django + factory_boy | latest |

---

## Telegram Bot

### Notification Types
- New AI recommendation (with approve/reject inline keyboard)
- Trade executed confirmation
- Stop-loss / take-profit triggered
- Daily portfolio summary
- Error alerts

### Commands
| Command | Description |
|---------|-------------|
| `/start` | Register chat ID for notifications |
| `/status` | Portfolio summary: balance, total value, daily P&L |
| `/positions` | List all open positions with unrealized P&L |
| `/pending` | List all pending AI recommendations |
| `/approve_<id>` | Approve recommendation → creates approved Order |
| `/reject_<id>` | Reject recommendation |
| `/buy <SYMBOL> <QTY>` | Manual market buy order |
| `/sell <SYMBOL> <QTY>` | Manual market sell order |
| `/report` | Trigger full daily report immediately |
| `/watchlist` | Show current watchlist |
| `/watchlist add <SYMBOL>` | Add symbol to watchlist |
| `/watchlist remove <SYMBOL>` | Remove symbol from watchlist |

---

## Security Considerations

- API keys stored in environment variables, never in code
- Telegram commands validated against registered chat IDs (whitelist)
- All order mutations require explicit approval (no auto-execute)
- Django CSRF protection on all state-changing endpoints
- Rate limiting on AI API calls via Celery task rate limits
- No real money at risk — PaperBroker only modifies local DB

---

## Future Extensions

| Feature | Approach |
|---------|---------|
| Real broker | Implement `AlpacaBroker(BaseBroker)`, set `BROKER_BACKEND=alpaca` |
| Backtesting | Add `BacktestEngine` that replays historical data through strategy |
| Options trading | Extend `Position` and `Order` models with options fields |
| Multi-user | Add user authentication, per-user portfolios and Telegram mappings |
| AI consensus | Auto-approve orders when ≥2 AI models agree (configurable threshold) |
| Mobile app | React Native frontend using same REST API |
