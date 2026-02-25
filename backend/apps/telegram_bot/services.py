"""
Telegram notification service.
Sends messages to the configured TELEGRAM_CHAT_ID.
Does NOT run the bot polling loop — that's in bot.py / management command.
"""
import logging

from django.conf import settings

logger = logging.getLogger(__name__)


class TelegramService:
    def __init__(self):
        self._token = settings.TELEGRAM_BOT_TOKEN
        self._chat_id = settings.TELEGRAM_CHAT_ID

    def _send(self, text: str) -> bool:
        """Send a message via Telegram Bot API. Returns True on success."""
        if not self._token or not self._chat_id:
            logger.debug("Telegram not configured — skipping notification")
            return False
        try:
            import requests
            url = f"https://api.telegram.org/bot{self._token}/sendMessage"
            resp = requests.post(
                url,
                json={"chat_id": self._chat_id, "text": text, "parse_mode": "HTML"},
                timeout=10,
            )
            resp.raise_for_status()
            return True
        except Exception as exc:
            logger.warning("Telegram send failed: %s", exc)
            return False

    def notify_recommendation(self, recommendation) -> bool:
        action_emoji = {
            "BUY": "📈",
            "SELL": "📉",
            "HOLD": "⏸",
            "REBALANCE": "🔄",
        }.get(recommendation.action, "📊")

        confidence_pct = float(recommendation.confidence) * 100
        text = (
            f"{action_emoji} <b>[{recommendation.provider}] {recommendation.action} "
            f"{recommendation.symbol}</b>\n"
            f"Confidence: {confidence_pct:.0f}%\n"
            f"Qty: {recommendation.quantity_suggested}\n"
        )
        if recommendation.price_target:
            text += f"Target: ${recommendation.price_target}\n"
        if recommendation.stop_loss:
            text += f"Stop-loss: ${recommendation.stop_loss}\n"
        text += f"\n💡 {recommendation.reasoning}\n\n"
        text += (
            f"<i>Tap /approve_{recommendation.id} or /reject_{recommendation.id}</i>"
        )
        return self._send(text)

    def notify_trade_executed(self, trade) -> bool:
        side_emoji = "🟢" if trade.side == "BUY" else "🔴"
        text = (
            f"{side_emoji} <b>Trade Executed</b>\n"
            f"{trade.side} {trade.quantity} {trade.symbol} @ ${trade.price}\n"
            f"Total: ${float(trade.quantity * trade.price):.2f}\n"
            f"Cash after: ${trade.portfolio_balance_after}"
        )
        return self._send(text)

    def notify_stop_loss(self, position, triggered_price) -> bool:
        text = (
            f"🛑 <b>Stop-Loss Triggered</b>\n"
            f"{position.symbol}: sold {position.quantity} shares @ ${triggered_price}\n"
            f"Protecting capital — position closed automatically."
        )
        return self._send(text)

    def notify_take_profit(self, position, triggered_price) -> bool:
        text = (
            f"✅ <b>Take-Profit Triggered</b>\n"
            f"{position.symbol}: sold {position.quantity} shares @ ${triggered_price}\n"
            f"Target reached — position closed with profit!"
        )
        return self._send(text)

    def send_daily_report(self, portfolio) -> bool:
        from apps.analytics.services import AnalyticsService
        svc = AnalyticsService()
        metrics = svc.get_portfolio_metrics(portfolio.id)

        text = (
            f"📊 <b>Daily Report — {portfolio.name}</b>\n\n"
            f"💰 Total Value: ${metrics.get('total_value', 0):,.2f}\n"
            f"💵 Cash: ${metrics.get('cash_balance', 0):,.2f}\n"
            f"📈 P&L: ${metrics.get('total_pnl', 0):+,.2f} "
            f"({metrics.get('total_pnl_pct', 0):+.2f}%)\n"
            f"🎯 Win Rate: {metrics.get('win_rate_pct', 0):.1f}%\n"
            f"📉 Max Drawdown: {metrics.get('max_drawdown_pct', 0):.1f}%\n"
            f"🔢 Trades: {metrics.get('total_trades', 0)}\n"
        )
        return self._send(text)

    def send_raw(self, text: str) -> bool:
        return self._send(text)
