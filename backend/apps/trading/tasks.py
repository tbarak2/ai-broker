"""Celery tasks for the trading app."""
import logging
from decimal import Decimal

from celery import shared_task

logger = logging.getLogger(__name__)


@shared_task(name="trading.execute_approved_orders")
def execute_approved_orders():
    """Execute all APPROVED orders via the broker."""
    from .services import TradingService
    svc = TradingService()
    trades = svc.execute_all_approved()
    logger.info("Executed %d orders", len(trades))
    return {"executed": len(trades)}


@shared_task(name="trading.check_stop_loss_take_profit")
def check_stop_loss_take_profit():
    """
    Check all open positions against stop-loss / take-profit thresholds
    defined in StrategyConfig. Auto-create APPROVED sell orders when triggered.
    """
    from apps.portfolio.models import Position
    from apps.ai_advisor.models import StrategyConfig
    from apps.market_data.services import MarketDataService
    from core.events.signals import stop_loss_triggered, take_profit_triggered
    from .services import TradingService

    market_svc = MarketDataService()
    trading_svc = TradingService()
    triggered = 0

    for position in Position.objects.filter(quantity__gt=0).select_related("portfolio"):
        try:
            config = StrategyConfig.objects.filter(
                portfolio=position.portfolio
            ).first()
            if not config:
                continue

            price_data = market_svc.get_current_price(position.symbol)
            current_price = price_data.price

            # Find any pending AI recommendation for this symbol with stop/take levels
            from apps.ai_advisor.models import AIRecommendation
            rec = AIRecommendation.objects.filter(
                portfolio=position.portfolio,
                symbol=position.symbol,
                status="EXECUTED",
            ).order_by("-created_at").first()

            if not rec:
                continue

            if rec.stop_loss and current_price <= Decimal(str(rec.stop_loss)):
                logger.warning(
                    "Stop-loss triggered: %s @ $%s (stop: $%s)",
                    position.symbol, current_price, rec.stop_loss,
                )
                order = trading_svc.create_manual_order(
                    portfolio_id=position.portfolio_id,
                    symbol=position.symbol,
                    side="SELL",
                    quantity=position.quantity,
                )
                trading_svc.approve_order(order.id)
                stop_loss_triggered.send(
                    sender="check_stop_loss_take_profit",
                    position=position,
                    triggered_price=current_price,
                )
                triggered += 1

            elif rec.take_profit and current_price >= Decimal(str(rec.take_profit)):
                logger.info(
                    "Take-profit triggered: %s @ $%s (target: $%s)",
                    position.symbol, current_price, rec.take_profit,
                )
                order = trading_svc.create_manual_order(
                    portfolio_id=position.portfolio_id,
                    symbol=position.symbol,
                    side="SELL",
                    quantity=position.quantity,
                )
                trading_svc.approve_order(order.id)
                take_profit_triggered.send(
                    sender="check_stop_loss_take_profit",
                    position=position,
                    triggered_price=current_price,
                )
                triggered += 1

        except Exception as exc:
            logger.exception(
                "Stop/take check failed for %s: %s", position.symbol, exc
            )

    return {"triggered": triggered}
