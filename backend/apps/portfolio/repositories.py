"""
Portfolio Repository — data access layer (Repository pattern).
Business logic never touches the ORM directly.
"""
from decimal import Decimal
from typing import Optional

from django.db import transaction
from django.db.models import QuerySet

from .models import Portfolio, Position


class PortfolioRepository:
    def get_by_id(self, portfolio_id: int) -> Portfolio:
        return Portfolio.objects.get(id=portfolio_id)

    def list_all(self) -> QuerySet[Portfolio]:
        return Portfolio.objects.prefetch_related("positions").all()

    def create(self, name: str, initial_capital: Decimal, user=None) -> Portfolio:
        return Portfolio.objects.create(
            name=name,
            initial_capital=initial_capital,
            cash_balance=initial_capital,
            user=user,
        )

    def update_cash_balance(
        self, portfolio_id: int, new_balance: Decimal
    ) -> None:
        Portfolio.objects.filter(id=portfolio_id).update(cash_balance=new_balance)

    def get_positions(self, portfolio_id: int) -> QuerySet[Position]:
        return Position.objects.filter(
            portfolio_id=portfolio_id, quantity__gt=0
        ).select_related("portfolio")

    def get_position(self, portfolio_id: int, symbol: str) -> Optional[Position]:
        return Position.objects.filter(
            portfolio_id=portfolio_id, symbol=symbol
        ).first()

    def upsert_position(
        self,
        portfolio_id: int,
        symbol: str,
        asset_type: str,
        quantity: Decimal,
        avg_cost_price: Decimal,
        current_price: Decimal,
    ) -> Position:
        position, _ = Position.objects.update_or_create(
            portfolio_id=portfolio_id,
            symbol=symbol,
            defaults={
                "asset_type": asset_type,
                "quantity": quantity,
                "avg_cost_price": avg_cost_price,
                "current_price": current_price,
            },
        )
        return position

    def update_current_prices(self, price_map: dict[str, Decimal]) -> None:
        """Bulk update current prices for all positions. price_map = {symbol: price}"""
        for symbol, price in price_map.items():
            Position.objects.filter(symbol=symbol, quantity__gt=0).update(
                current_price=price
            )
