import os
from celery import Celery
from celery.schedules import crontab

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "config.settings.local")

app = Celery("ai_broker")
app.config_from_object("django.conf:settings", namespace="CELERY")
app.autodiscover_tasks()

# --- Periodic Task Schedule ---
app.conf.beat_schedule = {
    # Fetch market prices every 5 minutes
    "fetch-market-prices": {
        "task": "market_data.fetch_market_prices",
        "schedule": 300,  # 5 minutes
    },
    # Run AI analysis every 30 minutes (all portfolios)
    "run-ai-analysis": {
        "task": "ai_advisor.run_analysis_all_portfolios",
        "schedule": 1800,  # 30 minutes
    },
    # Check stop-loss / take-profit every 5 minutes
    "check-stop-loss-take-profit": {
        "task": "trading.check_stop_loss_take_profit",
        "schedule": 300,
    },
    # Execute approved orders every minute
    "execute-approved-orders": {
        "task": "trading.execute_approved_orders",
        "schedule": 60,
    },
    # Daily report at 6:00 PM EST
    "send-daily-report": {
        "task": "telegram_bot.send_daily_report",
        "schedule": crontab(hour=18, minute=0),
    },
    # Expire old recommendations hourly
    "expire-old-recommendations": {
        "task": "ai_advisor.expire_old_recommendations",
        "schedule": crontab(minute=0),  # every hour
    },
}
