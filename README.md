# AI Broker

An AI-powered paper trading simulator that analyzes real market data and provides intelligent buy/sell/hold recommendations via Claude AI.

![Stack](https://img.shields.io/badge/Django-5.1-green) ![Stack](https://img.shields.io/badge/React-18-blue) ![Stack](https://img.shields.io/badge/Celery-5-orange) ![Stack](https://img.shields.io/badge/Docker-compose-blue)

## Features

- **Secure Login + 2FA** — JWT authentication with mandatory Google Authenticator (TOTP) two-factor auth
- **AI Recommendations** — Claude analyzes RSI, MACD, Bollinger Bands, and EMA indicators to suggest BUY / SELL / HOLD actions
- **Auto Management** — Optionally let the AI execute trades automatically when its confidence exceeds a configurable threshold (no manual approval needed)
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
./deploy.sh          # start (uses existing images)
./deploy.sh --build  # rebuild images then start
./deploy.sh --down   # stop everything, then restart fresh
```

- Frontend: http://localhost:5173
- Backend API: http://localhost:8010/api/

The script starts all services, waits for the backend to be ready, and runs any pending database migrations automatically.

### 4. Create your user account

There is no public registration. Create your account via the Django admin:

```bash
docker exec -it ai_broker-backend-1 python manage.py createsuperuser
```

Follow the prompts to set a username and password.

## Usage

1. Open http://localhost:5173 — you'll be redirected to the login page
2. Sign in with your username and password
3. **First login:** scan the QR code with Google Authenticator, then enter the 6-digit code to activate 2FA
4. **Subsequent logins:** enter the 6-digit code from the Authenticator app
5. Go to **Settings** → add stocks to your watchlist (e.g. AAPL, MSFT, NVDA)
3. Go to **AI Advisor** → click **Run Analysis**
6. Review recommendations and **Approve** or **Reject** them
7. Approved orders are executed automatically by the paper broker
8. Track your portfolio on the **Dashboard** and **Portfolio** pages

### Auto Management (optional)

Enable fully autonomous trading in **Settings → AI Strategy → Auto Management**:

- Toggle **Auto Management** on
- Set a **minimum confidence threshold** (default 70%, range 50–99%)
- Any BUY/SELL recommendation whose confidence meets the threshold will be executed immediately — no manual approval required
- HOLD and REBALANCE recommendations are never auto-executed

> **Note:** Auto management bypasses your manual review step. Only enable it if you trust the configured AI strategy and risk settings.

## Project Structure

```
ai-broker/
├── backend/
│   ├── apps/
│   │   ├── auth_app/        # JWT login + TOTP 2FA
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
