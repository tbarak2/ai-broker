"""Trading repository — all DB access for orders and trades."""
from decimal import Decimal
from typing import Optional
from django.db.models import QuerySet
from django.utils import timezone

from .models import Order, Trade


class OrderRepository:
    def get_by_id(self, order_id: int) -> Order:
        return Order.objects.select_related("portfolio", "ai_recommendation").get(
            id=order_id
        )

    def list_for_portfolio(
        self, portfolio_id: int, status: Optional[str] = None
    ) -> QuerySet[Order]:
        qs = Order.objects.filter(portfolio_id=portfolio_id).select_related(
            "portfolio"
        )
        if status:
            qs = qs.filter(status=status)
        return qs

    def list_approved(self) -> QuerySet[Order]:
        return Order.objects.filter(status=Order.Status.APPROVED).select_related(
            "portfolio"
        )

    def create_order(
        self,
        portfolio_id: int,
        symbol: str,
        side: str,
        quantity: Decimal,
        order_type: str = "MARKET",
        asset_type: str = "STOCK",
        limit_price: Optional[Decimal] = None,
        stop_price: Optional[Decimal] = None,
        source: str = "MANUAL",
        ai_recommendation_id: Optional[int] = None,
    ) -> Order:
        return Order.objects.create(
            portfolio_id=portfolio_id,
            symbol=symbol,
            side=side,
            quantity=quantity,
            order_type=order_type,
            asset_type=asset_type,
            limit_price=limit_price,
            stop_price=stop_price,
            source=source,
            ai_recommendation_id=ai_recommendation_id,
            status=Order.Status.PENDING_APPROVAL,
        )

    def mark_approved(self, order_id: int) -> None:
        Order.objects.filter(id=order_id).update(status=Order.Status.APPROVED)

    def mark_rejected(self, order_id: int, reason: str = "") -> None:
        Order.objects.filter(id=order_id).update(
            status=Order.Status.REJECTED, rejection_reason=reason
        )

    def mark_executed(
        self, order_id: int, executed_price: Decimal
    ) -> None:
        Order.objects.filter(id=order_id).update(
            status=Order.Status.EXECUTED,
            executed_price=executed_price,
            executed_at=timezone.now(),
        )

    def mark_failed(self, order_id: int, reason: str) -> None:
        Order.objects.filter(id=order_id).update(
            status=Order.Status.FAILED, rejection_reason=reason
        )


class TradeRepository:
    def create_trade(
        self,
        order: Order,
        portfolio_id: int,
        symbol: str,
        side: str,
        quantity: Decimal,
        price: Decimal,
        commission: Decimal,
        portfolio_balance_after: Decimal,
        executed_at,
    ) -> Trade:
        return Trade.objects.create(
            order=order,
            portfolio_id=portfolio_id,
            symbol=symbol,
            side=side,
            quantity=quantity,
            price=price,
            commission=commission,
            portfolio_balance_after=portfolio_balance_after,
            executed_at=executed_at,
        )

    def list_for_portfolio(self, portfolio_id: int) -> QuerySet[Trade]:
        return Trade.objects.filter(portfolio_id=portfolio_id).select_related("order")

    def get_recent(self, portfolio_id: int, limit: int = 10) -> QuerySet[Trade]:
        return self.list_for_portfolio(portfolio_id)[:limit]
