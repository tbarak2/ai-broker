# AI Broker

An AI-powered paper trading simulator that analyzes real market data and provides intelligent buy/sell/hold recommendations via Claude AI.

![Stack](https://img.shields.io/badge/Django-5.1-green) ![Stack](https://img.shields.io/badge/React-18-blue) ![Stack](https://img.shields.io/badge/Celery-5-orange) ![Stack](https://img.shields.io/badge/Docker-compose-blue)

## Features

- **AI Recommendations** — Claude analyzes RSI, MACD, Bollinger Bands, and EMA indicators to suggest BUY / SELL / HOLD actions
- **Real Market Data** — Live prices and historical OHLCV via Alpaca Markets API
- **Paper Trading** — Execute approved orders without real money; track P&L and positions
- **Telegram Bot** — Get notified on new recommendations and trade executions
- **Dashboard** — P&L chart, portfolio metrics, recent trades
- **Scheduled Analysis** — Celery Beat runs AI analysis every 30 minutes automatically

## Tech Stack

| Layer | Tech |
|-------|------|
| Backend | Django 5.1 + Django REST Framework |
| Frontend | React 18 + TypeScript + Vite + TanStack Query + Recharts + Tailwind |
| AI | Anthropic Claude (configurable: OpenAI, Gemini) |
| Market Data | Alpaca Markets API |
| Task Queue | Celery 5 + Celery Beat + Redis 7 |
| Database | PostgreSQL 16 |
| Containerization | Docker Compose |

## Quick Start

### 1. Clone & configure

```bash
git clone https://github.com/tbarak2/ai-broker.git
cd ai-broker
cp .env.example .env   # then fill in your API keys
```

### 2. Required API keys (in `.env`)

| Key | Where to get it |
|-----|----------------|
| `ANTHROPIC_API_KEY` | [console.anthropic.com](https://console.anthropic.com) |
| `ALPACA_API_KEY` + `ALPACA_SECRET_KEY` | [app.alpaca.markets](https://app.alpaca.markets) → Paper Trading |
| `TELEGRAM_BOT_TOKEN` | [@BotFather](https://t.me/botfather) on Telegram |
| `TELEGRAM_CHAT_ID` | Your Telegram user ID |

### 3. Start

```bash
docker compose up -d --build
```

- Frontend: http://localhost:5173
- Backend API: http://localhost:8010/api/

## Usage

1. Open http://localhost:5173
2. Go to **Settings** → add stocks to your watchlist (e.g. AAPL, MSFT, NVDA)
3. Go to **AI Advisor** → click **Run Analysis**
4. Review recommendations and **Approve** or **Reject** them
5. Approved orders are executed automatically by the paper broker
6. Track your portfolio on the **Dashboard** and **Portfolio** pages

## Project Structure

```
ai-broker/
├── backend/
│   ├── apps/
│   │   ├── ai_advisor/      # AI recommendations & strategy config
│   │   ├── analytics/       # P&L calculations & metrics
│   │   ├── market_data/     # Price snapshots & news
│   │   ├── portfolio/       # Portfolio & position management
│   │   ├── telegram_bot/    # Telegram notifications & commands
│   │   └── trading/         # Orders & trade execution
│   └── core/
│       ├── ai_providers/    # Claude / OpenAI / Gemini adapters
│       ├── brokers/         # Paper broker implementation
│       └── data_providers/  # Alpaca / yfinance adapters
└── frontend/
    └── src/
        ├── pages/           # Dashboard, Portfolio, AIAdvisor, Trades, Settings
        ├── hooks/           # TanStack Query hooks
        └── services/        # API client
```

## Environment Variables

See `.env.example` for the full list. Key variables:

```env
ANTHROPIC_API_KEY=         # Required for AI analysis
ALPACA_API_KEY=            # Required for market data
ALPACA_SECRET_KEY=
ALPACA_BASE_URL=https://paper-api.alpaca.markets
BROKER_BACKEND=paper       # "paper" only for now
AI_ANALYSIS_INTERVAL=30    # Minutes between auto-analyses
```

## License

MIT
