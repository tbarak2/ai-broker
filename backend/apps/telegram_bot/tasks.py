"""Celery tasks for the Telegram bot app."""
import logging

from celery import shared_task

logger = logging.getLogger(__name__)


@shared_task(name="telegram_bot.send_daily_report")
def send_daily_report():
    """Send a daily portfolio summary to Telegram. Scheduled at 18:00 EST."""
    from apps.portfolio.models import Portfolio
    from apps.telegram_bot.services import TelegramService

    svc = TelegramService()
    count = 0
    for portfolio in Portfolio.objects.all():
        try:
            svc.send_daily_report(portfolio)
            count += 1
        except Exception as exc:
            logger.warning("Daily report failed for portfolio %s: %s", portfolio.id, exc)

    return {"sent": count}
