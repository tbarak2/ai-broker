"""
Portfolio service — facade over repositories + broker (Facade pattern).
All business logic lives here; views/tasks call this, not models directly.
"""
import logging
from decimal import Decimal
from typing import Optional

from .repositories import PortfolioRepository

logger = logging.getLogger(__name__)


class PortfolioService:
    def __init__(self):
        self.repo = PortfolioRepository()

    def get_portfolio(self, portfolio_id: int):
        return self.repo.get_by_id(portfolio_id)

    def list_portfolios(self):
        return self.repo.list_all()

    def create_portfolio(self, name: str, initial_capital: Decimal, user=None):
        logger.info("Creating portfolio '%s' with $%s", name, initial_capital)
        return self.repo.create(name=name, initial_capital=initial_capital, user=user)

    def get_positions(self, portfolio_id: int):
        return self.repo.get_positions(portfolio_id)

    def update_prices(self, price_map: dict) -> None:
        """Bulk update current prices from market data cache."""
        self.repo.update_current_prices(price_map)

    def get_summary(self, portfolio_id: int) -> dict:
        portfolio = self.repo.get_by_id(portfolio_id)
        positions = self.repo.get_positions(portfolio_id)
        return {
            "id": portfolio.id,
            "name": portfolio.name,
            "cash_balance": float(portfolio.cash_balance),
            "total_value": float(portfolio.total_value),
            "total_pnl": float(portfolio.total_pnl),
            "total_pnl_pct": portfolio.total_pnl_pct,
            "positions_count": positions.count(),
        }
