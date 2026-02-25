"""
Trading signal receivers.
Connects trade_executed / order_approved signals to downstream consumers.
"""
from django.dispatch import receiver

from core.events.signals import trade_executed, order_approved


@receiver(trade_executed)
def on_trade_executed(sender, trade, **kwargs):
    """Send Telegram notification when a trade is executed."""
    try:
        from apps.telegram_bot.services import TelegramService
        TelegramService().notify_trade_executed(trade)
    except Exception:
        pass  # Telegram notification failure must never break trade execution


@receiver(order_approved)
def on_order_approved(sender, order, **kwargs):
    """Trigger immediate execution of approved orders via Celery."""
    try:
        from apps.trading.tasks import execute_approved_orders
        execute_approved_orders.delay()
    except Exception:
        pass
