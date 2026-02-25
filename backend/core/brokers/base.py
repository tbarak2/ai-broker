from abc import ABC, abstractmethod
from dataclasses import dataclass
from decimal import Decimal
from typing import Optional


@dataclass
class PositionData:
    symbol: str
    quantity: Decimal
    avg_cost_price: Decimal
    current_price: Decimal


@dataclass
class TradeResult:
    success: bool
    executed_price: Decimal
    executed_quantity: Decimal
    commission: Decimal
    error_message: Optional[str] = None


class BaseBroker(ABC):
    """
    Abstract broker interface (Adapter pattern).
    Both PaperBroker and future AlpacaBroker implement this interface.
    Switch brokers by changing BROKER_BACKEND in settings — zero business logic changes.
    """

    @abstractmethod
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
        """Execute a trade order and return the result."""
        ...

    @abstractmethod
    def get_position(self, portfolio_id: int, symbol: str) -> Optional[PositionData]:
        """Get the current position for a symbol in a portfolio."""
        ...

    @abstractmethod
    def get_account_balance(self, portfolio_id: int) -> Decimal:
        """Get the available cash balance for a portfolio."""
        ...

    @abstractmethod
    def cancel_order(self, order_id: int) -> bool:
        """Cancel a pending order. Returns True if successful."""
        ...
