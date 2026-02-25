import logging
from decimal import Decimal
from typing import Optional

from django.db import transaction
from django.utils import timezone

from .base import BaseBroker, PositionData, TradeResult

logger = logging.getLogger(__name__)


class PaperBroker(BaseBroker):
    """
    Paper trading broker — simulates trade execution using DB operations only.
    No external API calls. No real money at risk.

    When ready for real trading, replace with AlpacaBroker by changing
    BROKER_BACKEND=alpaca in settings.
    """

    def place_order(
        self,
        portfolio_id: int,
        symbol: str,
        side: str,
        quantity: Decimal,
        order_type: str = "MARKET",
        limit_price: Optional[Decimal] = None,
        stop_price: Optional[Decimal] = None,
    ) -> TradeResult:
        from apps.portfolio.models import Portfolio, Position
        from apps.market_data.services import MarketDataService

        try:
            with transaction.atomic():
                portfolio = Portfolio.objects.select_for_update().get(id=portfolio_id)
                market_svc = MarketDataService()
                current_price = market_svc.get_current_price(symbol)

                # For paper trading, always use current market price
                executed_price = current_price
                total_cost = executed_price * quantity
                commission = Decimal("0.00")  # Paper trading: no commissions

                if side == "BUY":
                    if portfolio.cash_balance < total_cost:
                        return TradeResult(
                            success=False,
                            executed_price=executed_price,
                            executed_quantity=quantity,
                            commission=commission,
                            error_message=(
                                f"Insufficient funds. Required: ${total_cost:.2f}, "
                                f"Available: ${portfolio.cash_balance:.2f}"
                            ),
                        )
                    portfolio.cash_balance -= total_cost
                    self._update_position_buy(portfolio, symbol, quantity, executed_price)

                elif side == "SELL":
                    position = self._get_position_obj(portfolio_id, symbol)
                    if not position or position.quantity < quantity:
                        available = position.quantity if position else Decimal("0")
                        return TradeResult(
                            success=False,
                            executed_price=executed_price,
                            executed_quantity=quantity,
                            commission=commission,
                            error_message=(
                                f"Insufficient shares. Required: {quantity}, "
                                f"Available: {available}"
                            ),
                        )
                    portfolio.cash_balance += executed_price * quantity
                    self._update_position_sell(position, quantity, executed_price)

                portfolio.save()
                logger.info(
                    "Paper trade executed: %s %s %s @ $%s",
                    side, quantity, symbol, executed_price
                )
                return TradeResult(
                    success=True,
                    executed_price=executed_price,
                    executed_quantity=quantity,
                    commission=commission,
                )

        except Portfolio.DoesNotExist:
            return TradeResult(
                success=False,
                executed_price=Decimal("0"),
                executed_quantity=quantity,
                commission=Decimal("0"),
                error_message=f"Portfolio {portfolio_id} not found",
            )
        except Exception as exc:
            logger.exception("Paper broker error: %s", exc)
            return TradeResult(
                success=False,
                executed_price=Decimal("0"),
                executed_quantity=quantity,
                commission=Decimal("0"),
                error_message=str(exc),
            )

    def get_position(self, portfolio_id: int, symbol: str) -> Optional[PositionData]:
        pos = self._get_position_obj(portfolio_id, symbol)
        if not pos:
            return None
        return PositionData(
            symbol=pos.symbol,
            quantity=pos.quantity,
            avg_cost_price=pos.avg_cost_price,
            current_price=pos.current_price,
        )

    def get_account_balance(self, portfolio_id: int) -> Decimal:
        from apps.portfolio.models import Portfolio
        return Portfolio.objects.get(id=portfolio_id).cash_balance

    def cancel_order(self, order_id: int) -> bool:
        from apps.trading.models import Order
        updated = Order.objects.filter(
            id=order_id, status="APPROVED"
        ).update(status="CANCELLED")
        return bool(updated)

    def _get_position_obj(self, portfolio_id: int, symbol: str):
        from apps.portfolio.models import Position
        return Position.objects.filter(
            portfolio_id=portfolio_id, symbol=symbol, quantity__gt=0
        ).first()

    def _update_position_buy(
        self, portfolio, symbol: str, quantity: Decimal, price: Decimal
    ):
        from apps.portfolio.models import Position
        position, created = Position.objects.get_or_create(
            portfolio=portfolio,
            symbol=symbol,
            defaults={
                "asset_type": "STOCK",
                "quantity": Decimal("0"),
                "avg_cost_price": price,
                "current_price": price,
            },
        )
        if not created:
            # Weighted average cost
            total_cost = position.avg_cost_price * position.quantity + price * quantity
            position.quantity += quantity
            position.avg_cost_price = total_cost / position.quantity
            position.current_price = price
        else:
            position.quantity = quantity
        position.save()

    def _update_position_sell(self, position, quantity: Decimal, price: Decimal):
        realized_pnl = (price - position.avg_cost_price) * quantity
        position.realized_pnl += realized_pnl
        position.quantity -= quantity
        position.current_price = price
        position.save()
