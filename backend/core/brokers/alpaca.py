"""
AlpacaBroker — Real money broker via Alpaca API.

NOT YET IMPLEMENTED. This is a placeholder that will be filled in
when transitioning from paper to live trading.

To activate: set BROKER_BACKEND=alpaca in .env
"""
from decimal import Decimal
from typing import Optional

from .base import BaseBroker, PositionData, TradeResult


class AlpacaBroker(BaseBroker):
    """Real Alpaca broker. Implement when ready for live trading."""

    def place_order(self, portfolio_id, symbol, side, quantity, order_type="MARKET",
                    limit_price=None, stop_price=None) -> TradeResult:
        raise NotImplementedError("AlpacaBroker not yet implemented. Use BROKER_BACKEND=paper")

    def get_position(self, portfolio_id, symbol) -> Optional[PositionData]:
        raise NotImplementedError

    def get_account_balance(self, portfolio_id) -> Decimal:
        raise NotImplementedError

    def cancel_order(self, order_id) -> bool:
        raise NotImplementedError
