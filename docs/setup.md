# AI Broker — Local Setup Guide

## Prerequisites

- Docker Desktop (or Docker Engine + Docker Compose v2)
- Git

That's it. Everything else runs inside containers.

---

## 1. Clone & Configure Environment

```bash
git clone <repo-url> ai_broker
cd ai_broker
cp .env.example .env
```

Edit `.env` and fill in your API keys (see **API Keys** section below).

---

## 2. Start All Services

```bash
docker compose up --build
```

This starts:
| Service | Port | Description |
|---------|------|-------------|
| `backend` | 8000 | Django DRF API |
| `frontend` | 5173 | React Vite dev server |
| `db` | 5432 | PostgreSQL |
| `redis` | 6379 | Redis (queue + cache) |
| `celery` | — | Celery worker |
| `celery-beat` | — | Celery scheduler |
| `telegram-bot` | — | Telegram bot process |

On first start, Django automatically runs migrations.

---

## 3. Access the App

| URL | Service |
|-----|---------|
| http://localhost:5173 | React frontend |
| http://localhost:8000/api | Django REST API |
| http://localhost:8000/admin | Django admin |

Create a superuser for the admin panel:
```bash
docker compose exec backend python manage.py createsuperuser
```

---

## 4. Create Your First Portfolio

Via the UI: Go to http://localhost:5173 → click **New Portfolio** → enter a name and starting capital (e.g. $10,000).

Via API:
```bash
curl -X POST http://localhost:8000/api/portfolio/ \
  -H "Content-Type: application/json" \
  -d '{"name": "My Portfolio", "initial_capital": 10000}'
```

---

## 5. Configure Your Watchlist & AI Settings

Go to **Settings** in the UI and configure:
- Which AI providers to use (Claude, OpenAI, Gemini)
- Which analysis strategies to run (technical, sentiment, fundamental, rebalancing)
- Risk tolerance (LOW / MEDIUM / HIGH)
- Max position size (% of portfolio per position)
- Watchlist (stock symbols to monitor)

---

## API Keys

You need accounts and API keys for the services you want to use.

### Required (at least one AI provider)

| Service | Where to get | `.env` key |
|---------|-------------|-----------|
| **Anthropic Claude** | https://console.anthropic.com | `ANTHROPIC_API_KEY` |
| **OpenAI** | https://platform.openai.com | `OPENAI_API_KEY` |
| **Google Gemini** | https://makersuite.google.com | `GEMINI_API_KEY` |

### Required (market data)

| Service | Where to get | `.env` keys | Notes |
|---------|-------------|-------------|-------|
| **Alpaca** | https://alpaca.markets | `ALPACA_API_KEY`, `ALPACA_SECRET_KEY` | Free paper trading account. Use Paper API URL. |

### Optional

| Service | Where to get | `.env` key | Notes |
|---------|-------------|-----------|-------|
| **Alpha Vantage** | https://www.alphavantage.co | `ALPHA_VANTAGE_API_KEY` | News & sentiment. Free tier: 25 req/day |

### Telegram Bot Setup

1. Open Telegram, search for **@BotFather**
2. Send `/newbot` and follow prompts to create a bot
3. Copy the bot token → `TELEGRAM_BOT_TOKEN` in `.env`
4. Start a conversation with your bot
5. Run this to get your chat ID:
   ```bash
   curl https://api.telegram.org/bot<YOUR_TOKEN>/getUpdates
   ```
6. Copy your `chat.id` → `TELEGRAM_CHAT_ID` in `.env`
7. Restart the `telegram-bot` service:
   ```bash
   docker compose restart telegram-bot
   ```

---

## Environment Variables Reference

```env
# Django
SECRET_KEY=change-me-in-production
DEBUG=True
ALLOWED_HOSTS=localhost,127.0.0.1
DATABASE_URL=postgresql://broker:broker@db:5432/broker_db
DJANGO_SETTINGS_MODULE=config.settings.local

# Redis
REDIS_URL=redis://redis:6379/0

# AI Providers (configure at least one)
ANTHROPIC_API_KEY=
OPENAI_API_KEY=
GEMINI_API_KEY=

# Market Data — Alpaca (required)
ALPACA_API_KEY=
ALPACA_SECRET_KEY=
ALPACA_BASE_URL=https://paper-api.alpaca.markets

# Market Data — Alpha Vantage (optional, for news)
ALPHA_VANTAGE_API_KEY=

# Telegram (optional but highly recommended)
TELEGRAM_BOT_TOKEN=
TELEGRAM_CHAT_ID=

# Broker mode: "paper" (default) or "alpaca" (future real trading)
BROKER_BACKEND=paper

# Analysis schedule (minutes between AI analysis runs)
AI_ANALYSIS_INTERVAL=30

# CORS (for frontend dev)
CORS_ALLOWED_ORIGINS=http://localhost:5173
```

---

## Common Commands

```bash
# Start everything
docker compose up

# Start in background
docker compose up -d

# View logs for a specific service
docker compose logs -f backend
docker compose logs -f celery

# Run Django management commands
docker compose exec backend python manage.py migrate
docker compose exec backend python manage.py shell

# Manually trigger AI analysis
docker compose exec backend python manage.py shell -c "
from apps.ai_advisor.tasks import run_ai_analysis_task
run_ai_analysis_task.delay(portfolio_id=1)
"

# Manually trigger market data fetch
docker compose exec backend python manage.py shell -c "
from apps.market_data.tasks import fetch_market_prices
fetch_market_prices.delay()
"

# View Celery task queue
docker compose exec backend celery -A config.celery inspect active

# Reset and rebuild everything (WARNING: deletes all data)
docker compose down -v && docker compose up --build

# Run backend tests
docker compose exec backend pytest

# Frontend — install new package
docker compose exec frontend npm install <package>
```

---

## Troubleshooting

### Celery tasks not running
```bash
docker compose logs celery
docker compose logs celery-beat
# Ensure REDIS_URL is correct in .env
```

### Alpaca API errors
- Verify you're using the paper trading URL: `https://paper-api.alpaca.markets`
- Check your key/secret are for the paper account (separate from live account)

### AI provider errors
- Verify API keys are set in `.env`
- Check rate limits — analysis runs every 30 min by default
- If one provider fails, others continue independently

### Telegram bot not responding
- Ensure `TELEGRAM_BOT_TOKEN` and `TELEGRAM_CHAT_ID` are set
- Check that you've started a conversation with the bot on Telegram
- Restart: `docker compose restart telegram-bot`
- View logs: `docker compose logs telegram-bot`

### Database connection errors on first start
PostgreSQL may not be ready when Django starts. The backend container retries automatically. If it persists:
```bash
docker compose restart backend
```

---

## Development Tips

### Hot reload
Both backend (Django dev server) and frontend (Vite) support hot reload out of the box when running via Docker Compose.

### Django shell
```bash
docker compose exec backend python manage.py shell_plus
# (django-extensions provides shell_plus with all models auto-imported)
```

### Viewing the Celery task schedule
The Beat schedule is defined in `backend/config/celery.py`. Edit it and restart `celery-beat` to change task frequencies.

### Switching AI providers
In the Settings page, toggle AI providers on/off. Or edit `StrategyConfig` directly via the admin panel or API.
