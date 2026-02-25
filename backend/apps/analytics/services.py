"""
Analytics service — computes portfolio performance metrics and P&L history.
No models: works purely from Trade and Position records.
"""
import logging
import math
from decimal import Decimal
from typing import List

from django.utils import timezone

logger = logging.getLogger(__name__)


class AnalyticsService:
    def get_pnl_history(self, portfolio_id: int, period: str = "30d") -> List[dict]:
        """
        Return daily P&L data points for charting.
        Each point: {date: str, portfolio_value: float, daily_pnl: float}
        Derived from Trade records + current portfolio state.
        """
        from apps.trading.models import Trade
        from apps.portfolio.models import Portfolio

        try:
            portfolio = Portfolio.objects.get(id=portfolio_id)
        except Portfolio.DoesNotExist:
            return []

        days = self._parse_period_days(period)
        since = timezone.now() - timezone.timedelta(days=days)

        trades = list(
            Trade.objects.filter(
                portfolio_id=portfolio_id,
                executed_at__gte=since,
            ).order_by("executed_at")
        )

        # Build daily snapshots from trade history
        daily = {}
        running_balance = float(portfolio.cash_balance)

        # Work backwards from current state
        if not trades:
            # No trades: flat line from initial capital to now
            initial = float(portfolio.initial_capital)
            current = float(portfolio.total_value)
            result = []
            for i in range(days):
                d = (timezone.now() - timezone.timedelta(days=days - i)).date()
                # Linear interpolation (simplified)
                frac = i / max(days - 1, 1)
                result.append({
                    "date": d.isoformat(),
                    "portfolio_value": round(initial + (current - initial) * frac, 2),
                    "daily_pnl": 0.0,
                })
            return result

        for trade in trades:
            date_str = trade.executed_at.date().isoformat()
            if date_str not in daily:
                daily[date_str] = {
                    "date": date_str,
                    "portfolio_value": float(trade.portfolio_balance_after),
                    "daily_pnl": 0.0,
                }
            else:
                daily[date_str]["portfolio_value"] = float(trade.portfolio_balance_after)

        # Compute daily_pnl as difference from previous day
        sorted_dates = sorted(daily.keys())
        for i, date_str in enumerate(sorted_dates):
            if i == 0:
                daily[date_str]["daily_pnl"] = 0.0
            else:
                prev = daily[sorted_dates[i - 1]]["portfolio_value"]
                curr = daily[date_str]["portfolio_value"]
                daily[date_str]["daily_pnl"] = round(curr - prev, 2)

        return [daily[d] for d in sorted_dates]

    def get_portfolio_metrics(self, portfolio_id: int) -> dict:
        """
        Compute: total P&L, win rate, best/worst trade, Sharpe ratio (approx),
        max drawdown, number of trades.
        """
        from apps.trading.models import Trade
        from apps.portfolio.models import Portfolio

        try:
            portfolio = Portfolio.objects.get(id=portfolio_id)
        except Portfolio.DoesNotExist:
            return {}

        trades = list(
            Trade.objects.filter(portfolio_id=portfolio_id).order_by("executed_at")
        )

        total_trades = len(trades)
        sell_trades = [t for t in trades if t.side == "SELL"]
        wins = 0
        pnl_list = []

        for t in sell_trades:
            # Approx: find matching buy trade for this symbol
            buy_trades = [
                b for b in trades
                if b.symbol == t.symbol and b.side == "BUY" and b.executed_at < t.executed_at
            ]
            if buy_trades:
                avg_buy = sum(float(b.price) for b in buy_trades) / len(buy_trades)
                trade_pnl = (float(t.price) - avg_buy) * float(t.quantity)
                pnl_list.append(trade_pnl)
                if trade_pnl > 0:
                    wins += 1

        win_rate = (wins / len(sell_trades) * 100) if sell_trades else 0.0
        best_trade = max(pnl_list) if pnl_list else 0.0
        worst_trade = min(pnl_list) if pnl_list else 0.0

        # Sharpe ratio (simplified, using daily portfolio_balance_after)
        sharpe = self._compute_sharpe(trades)

        # Max drawdown
        max_drawdown = self._compute_max_drawdown(trades, float(portfolio.initial_capital))

        return {
            "total_pnl": float(portfolio.total_pnl),
            "total_pnl_pct": portfolio.total_pnl_pct,
            "total_value": float(portfolio.total_value),
            "cash_balance": float(portfolio.cash_balance),
            "total_trades": total_trades,
            "sell_trades": len(sell_trades),
            "win_rate_pct": round(win_rate, 1),
            "best_trade_pnl": round(best_trade, 2),
            "worst_trade_pnl": round(worst_trade, 2),
            "sharpe_ratio": sharpe,
            "max_drawdown_pct": max_drawdown,
        }

    def _parse_period_days(self, period: str) -> int:
        mapping = {"7d": 7, "30d": 30, "90d": 90, "1y": 365, "ytd": 365}
        return mapping.get(period.lower(), 30)

    def _compute_sharpe(self, trades, risk_free_rate: float = 0.05) -> float:
        """Rough Sharpe using trade P&L returns."""
        if len(trades) < 2:
            return 0.0
        balances = [float(t.portfolio_balance_after) for t in trades]
        returns = [
            (balances[i] - balances[i - 1]) / balances[i - 1]
            for i in range(1, len(balances))
            if balances[i - 1] != 0
        ]
        if not returns:
            return 0.0
        avg_return = sum(returns) / len(returns)
        variance = sum((r - avg_return) ** 2 for r in returns) / len(returns)
        std_dev = math.sqrt(variance) if variance > 0 else 0
        if std_dev == 0:
            return 0.0
        daily_rf = risk_free_rate / 252
        return round((avg_return - daily_rf) / std_dev * math.sqrt(252), 2)

    def _compute_max_drawdown(self, trades, initial_capital: float) -> float:
        """Compute max drawdown % from peak."""
        if not trades:
            return 0.0
        balances = [initial_capital] + [float(t.portfolio_balance_after) for t in trades]
        peak = balances[0]
        max_dd = 0.0
        for b in balances:
            if b > peak:
                peak = b
            dd = (peak - b) / peak * 100 if peak > 0 else 0
            max_dd = max(max_dd, dd)
        return round(max_dd, 2)
