"""
Telegram signal receivers.
Listens to core event signals and delegates to TelegramService.
"""
from django.dispatch import receiver

from core.events.signals import (
    recommendation_created,
    stop_loss_triggered,
    take_profit_triggered,
)


@receiver(recommendation_created)
def on_recommendation_created(sender, recommendation, **kwargs):
    try:
        from .services import TelegramService
        TelegramService().notify_recommendation(recommendation)
    except Exception:
        pass


@receiver(stop_loss_triggered)
def on_stop_loss_triggered(sender, position, triggered_price, **kwargs):
    try:
        from .services import TelegramService
        TelegramService().notify_stop_loss(position, triggered_price)
    except Exception:
        pass


@receiver(take_profit_triggered)
def on_take_profit_triggered(sender, position, triggered_price, **kwargs):
    try:
        from .services import TelegramService
        TelegramService().notify_take_profit(position, triggered_price)
    except Exception:
        pass
