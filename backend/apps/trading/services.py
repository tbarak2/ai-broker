"""
Trading service — coordinates order approval, execution, and trade recording.
Uses the broker abstraction so paper ↔ real swap is transparent.
"""
import logging
from decimal import Decimal
from typing import Optional

from django.utils import timezone

from core.brokers.factory import get_broker
from core.events.signals import order_approved, trade_executed
from .models import Order, Trade
from .repositories import OrderRepository, TradeRepository

logger = logging.getLogger(__name__)


class TradingService:
    def __init__(self):
        self.order_repo = OrderRepository()
        self.trade_repo = TradeRepository()
        self.broker = get_broker()

    def create_manual_order(
        self,
        portfolio_id: int,
        symbol: str,
        side: str,
        quantity: Decimal,
        order_type: str = "MARKET",
        asset_type: str = "STOCK",
        limit_price: Optional[Decimal] = None,
        stop_price: Optional[Decimal] = None,
    ) -> Order:
        order = self.order_repo.create_order(
            portfolio_id=portfolio_id,
            symbol=symbol,
            side=side,
            quantity=quantity,
            order_type=order_type,
            asset_type=asset_type,
            limit_price=limit_price,
            stop_price=stop_price,
            source=Order.Source.MANUAL,
        )
        logger.info("Manual order created: %s", order)
        return order

    def create_ai_order(
        self,
        portfolio_id: int,
        symbol: str,
        side: str,
        quantity: Decimal,
        ai_recommendation_id: int,
        asset_type: str = "STOCK",
    ) -> Order:
        order = self.order_repo.create_order(
            portfolio_id=portfolio_id,
            symbol=symbol,
            side=side,
            quantity=quantity,
            source=Order.Source.AI_SUGGESTED,
            ai_recommendation_id=ai_recommendation_id,
            asset_type=asset_type,
        )
        logger.info("AI-suggested order created: %s", order)
        return order

    def approve_order(self, order_id: int) -> Order:
        order = self.order_repo.get_by_id(order_id)
        if order.status != Order.Status.PENDING_APPROVAL:
            raise ValueError(
                f"Order {order_id} is in status {order.status}, cannot approve"
            )
        self.order_repo.mark_approved(order_id)
        order.refresh_from_db()
        order_approved.send(sender=self.__class__, order=order)
        logger.info("Order %s approved", order_id)
        return order

    def reject_order(self, order_id: int, reason: str = "") -> Order:
        order = self.order_repo.get_by_id(order_id)
        if order.status not in (
            Order.Status.PENDING_APPROVAL,
            Order.Status.APPROVED,
        ):
            raise ValueError(
                f"Order {order_id} is in status {order.status}, cannot reject"
            )
        self.order_repo.mark_rejected(order_id, reason)
        order.refresh_from_db()
        logger.info("Order %s rejected: %s", order_id, reason)
        return order

    def execute_order(self, order_id: int) -> Trade:
        """Execute an APPROVED order via the broker and record the trade."""
        order = self.order_repo.get_by_id(order_id)
        if order.status != Order.Status.APPROVED:
            raise ValueError(
                f"Order {order_id} must be APPROVED to execute (current: {order.status})"
            )

        result = self.broker.place_order(
            portfolio_id=order.portfolio_id,
            symbol=order.symbol,
            side=order.side,
            quantity=order.quantity,
            order_type=order.order_type,
            limit_price=order.limit_price,
            stop_price=order.stop_price,
        )

        if not result.success:
            self.order_repo.mark_failed(order_id, result.error_message or "Unknown error")
            raise RuntimeError(f"Order execution failed: {result.error_message}")

        self.order_repo.mark_executed(order_id, result.executed_price)

        # Reload the updated portfolio balance
        from apps.portfolio.models import Portfolio
        portfolio = Portfolio.objects.get(id=order.portfolio_id)

        trade = self.trade_repo.create_trade(
            order=order,
            portfolio_id=order.portfolio_id,
            symbol=order.symbol,
            side=order.side,
            quantity=result.executed_quantity,
            price=result.executed_price,
            commission=result.commission,
            portfolio_balance_after=portfolio.cash_balance,
            executed_at=timezone.now(),
        )

        trade_executed.send(sender=self.__class__, trade=trade)
        logger.info("Trade executed: %s", trade)
        return trade

    def execute_all_approved(self) -> list[Trade]:
        """Execute all pending APPROVED orders (called by Celery task)."""
        orders = self.order_repo.list_approved()
        trades = []
        for order in orders:
            try:
                trade = self.execute_order(order.id)
                trades.append(trade)
            except Exception as exc:
                logger.error("Failed to execute order %s: %s", order.id, exc)
        return trades

    def cancel_order(self, order_id: int) -> Order:
        order = self.order_repo.get_by_id(order_id)
        if order.status in (Order.Status.EXECUTED, Order.Status.CANCELLED):
            raise ValueError(f"Cannot cancel order in status {order.status}")
        self.broker.cancel_order(order_id)
        Order.objects.filter(id=order_id).update(status=Order.Status.CANCELLED)
        order.refresh_from_db()
        return order
