"""
Telegram bot command handlers using python-telegram-bot v21.
Each handler is an async function registered in bot.py.
"""
import logging
from decimal import Decimal, InvalidOperation

from telegram import Update
from telegram.ext import ContextTypes

logger = logging.getLogger(__name__)


def _get_default_portfolio_id() -> int:
    """Return the first portfolio ID (single-portfolio setup)."""
    from apps.portfolio.models import Portfolio
    p = Portfolio.objects.first()
    if not p:
        raise ValueError("No portfolio found. Create one via the API first.")
    return p.id


async def cmd_start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "🤖 <b>AI Broker Bot</b> ready!\n\n"
        "Commands:\n"
        "/status — portfolio summary\n"
        "/positions — open positions\n"
        "/pending — pending AI recommendations\n"
        "/approve_&lt;id&gt; — approve a recommendation\n"
        "/reject_&lt;id&gt; — reject a recommendation\n"
        "/buy SYMBOL QTY — manual buy order\n"
        "/sell SYMBOL QTY — manual sell order\n"
        "/report — daily summary",
        parse_mode="HTML",
    )


async def cmd_status(update: Update, context: ContextTypes.DEFAULT_TYPE):
    try:
        from apps.portfolio.services import PortfolioService
        svc = PortfolioService()
        portfolio_id = _get_default_portfolio_id()
        summary = svc.get_summary(portfolio_id)
        text = (
            f"📊 <b>{summary['name']}</b>\n\n"
            f"💰 Total: ${summary['total_value']:,.2f}\n"
            f"💵 Cash: ${summary['cash_balance']:,.2f}\n"
            f"📈 P&L: ${summary['total_pnl']:+,.2f} ({summary['total_pnl_pct']:+.2f}%)\n"
            f"📦 Positions: {summary['positions_count']}"
        )
    except Exception as exc:
        text = f"❌ Error: {exc}"
    await update.message.reply_text(text, parse_mode="HTML")


async def cmd_positions(update: Update, context: ContextTypes.DEFAULT_TYPE):
    try:
        from apps.portfolio.repositories import PortfolioRepository
        repo = PortfolioRepository()
        portfolio_id = _get_default_portfolio_id()
        positions = repo.get_positions(portfolio_id)
        if not positions:
            text = "📭 No open positions"
        else:
            lines = ["<b>Open Positions</b>\n"]
            for pos in positions:
                emoji = "🟢" if pos.unrealized_pnl >= 0 else "🔴"
                lines.append(
                    f"{emoji} <b>{pos.symbol}</b> x{pos.quantity}\n"
                    f"   Avg: ${pos.avg_cost_price} | Now: ${pos.current_price}\n"
                    f"   P&L: ${pos.unrealized_pnl:+.2f} ({pos.unrealized_pnl_pct:+.1f}%)"
                )
            text = "\n\n".join(lines)
    except Exception as exc:
        text = f"❌ Error: {exc}"
    await update.message.reply_text(text, parse_mode="HTML")


async def cmd_pending(update: Update, context: ContextTypes.DEFAULT_TYPE):
    try:
        from apps.ai_advisor.models import AIRecommendation
        portfolio_id = _get_default_portfolio_id()
        recs = AIRecommendation.objects.filter(
            portfolio_id=portfolio_id, status="PENDING"
        ).order_by("-created_at")[:10]

        if not recs:
            text = "📭 No pending recommendations"
        else:
            lines = [f"<b>Pending Recommendations ({recs.count()})</b>\n"]
            for rec in recs:
                confidence_pct = float(rec.confidence) * 100
                lines.append(
                    f"#{rec.id} [{rec.provider}] <b>{rec.action} {rec.symbol}</b>\n"
                    f"   Confidence: {confidence_pct:.0f}% | Qty: {rec.quantity_suggested}\n"
                    f"   {rec.reasoning[:80]}...\n"
                    f"   /approve_{rec.id} | /reject_{rec.id}"
                )
            text = "\n\n".join(lines)
    except Exception as exc:
        text = f"❌ Error: {exc}"
    await update.message.reply_text(text, parse_mode="HTML")


async def cmd_approve(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle /approve_<id> commands."""
    try:
        rec_id = int(context.args[0]) if context.args else None
        if rec_id is None:
            # Parse from command text: /approve_42
            command = update.message.text.split("@")[0]
            rec_id = int(command.split("_")[1])

        from apps.ai_advisor.services import AIAdvisorService
        svc = AIAdvisorService()
        rec = svc.approve_recommendation(rec_id)
        await update.message.reply_text(
            f"✅ Recommendation #{rec_id} approved!\n"
            f"{rec.action} {rec.quantity_suggested} {rec.symbol} order queued."
        )
    except (ValueError, IndexError) as exc:
        await update.message.reply_text(f"❌ Error: {exc}")
    except Exception as exc:
        logger.exception("Approve failed: %s", exc)
        await update.message.reply_text(f"❌ Error: {exc}")


async def cmd_reject(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle /reject_<id> commands."""
    try:
        command = update.message.text.split("@")[0]
        rec_id = int(command.split("_")[1])

        from apps.ai_advisor.services import AIAdvisorService
        svc = AIAdvisorService()
        svc.reject_recommendation(rec_id)
        await update.message.reply_text(f"🚫 Recommendation #{rec_id} rejected.")
    except (ValueError, IndexError) as exc:
        await update.message.reply_text(f"❌ Error: {exc}")
    except Exception as exc:
        await update.message.reply_text(f"❌ Error: {exc}")


async def cmd_buy(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle /buy SYMBOL QTY"""
    try:
        if len(context.args) < 2:
            await update.message.reply_text("Usage: /buy SYMBOL QUANTITY")
            return
        symbol = context.args[0].upper()
        quantity = Decimal(context.args[1])
        portfolio_id = _get_default_portfolio_id()

        from apps.trading.services import TradingService
        svc = TradingService()
        order = svc.create_manual_order(
            portfolio_id=portfolio_id,
            symbol=symbol,
            side="BUY",
            quantity=quantity,
        )
        svc.approve_order(order.id)
        await update.message.reply_text(
            f"🟢 BUY order #{order.id} created for {quantity} {symbol}.\n"
            f"Executing now..."
        )
    except (InvalidOperation, ValueError) as exc:
        await update.message.reply_text(f"❌ Error: {exc}")
    except Exception as exc:
        logger.exception("Buy command failed: %s", exc)
        await update.message.reply_text(f"❌ Error: {exc}")


async def cmd_sell(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle /sell SYMBOL QTY"""
    try:
        if len(context.args) < 2:
            await update.message.reply_text("Usage: /sell SYMBOL QUANTITY")
            return
        symbol = context.args[0].upper()
        quantity = Decimal(context.args[1])
        portfolio_id = _get_default_portfolio_id()

        from apps.trading.services import TradingService
        svc = TradingService()
        order = svc.create_manual_order(
            portfolio_id=portfolio_id,
            symbol=symbol,
            side="SELL",
            quantity=quantity,
        )
        svc.approve_order(order.id)
        await update.message.reply_text(
            f"🔴 SELL order #{order.id} created for {quantity} {symbol}.\n"
            f"Executing now..."
        )
    except (InvalidOperation, ValueError) as exc:
        await update.message.reply_text(f"❌ Error: {exc}")
    except Exception as exc:
        logger.exception("Sell command failed: %s", exc)
        await update.message.reply_text(f"❌ Error: {exc}")


async def cmd_report(update: Update, context: ContextTypes.DEFAULT_TYPE):
    from apps.portfolio.models import Portfolio
    from apps.telegram_bot.services import TelegramService
    portfolio = Portfolio.objects.first()
    if not portfolio:
        await update.message.reply_text("❌ No portfolio found")
        return
    TelegramService().send_daily_report(portfolio)
    await update.message.reply_text("📊 Daily report sent!")


async def cmd_watchlist(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle /watchlist add TSLA or /watchlist remove TSLA or /watchlist"""
    try:
        from apps.ai_advisor.models import StrategyConfig
        portfolio_id = _get_default_portfolio_id()
        config = StrategyConfig.objects.filter(portfolio_id=portfolio_id).first()
        if not config:
            await update.message.reply_text("❌ No strategy config found")
            return

        if not context.args:
            symbols = config.watchlist or []
            text = "📋 <b>Watchlist</b>\n" + "\n".join(f"  • {s}" for s in symbols)
            await update.message.reply_text(text, parse_mode="HTML")
            return

        action = context.args[0].lower()
        if len(context.args) < 2:
            await update.message.reply_text("Usage: /watchlist add SYMBOL | /watchlist remove SYMBOL")
            return

        symbol = context.args[1].upper()
        watchlist = list(config.watchlist or [])

        if action == "add":
            if symbol not in watchlist:
                watchlist.append(symbol)
                config.watchlist = watchlist
                config.save(update_fields=["watchlist"])
                await update.message.reply_text(f"✅ {symbol} added to watchlist")
            else:
                await update.message.reply_text(f"ℹ️ {symbol} already in watchlist")
        elif action == "remove":
            if symbol in watchlist:
                watchlist.remove(symbol)
                config.watchlist = watchlist
                config.save(update_fields=["watchlist"])
                await update.message.reply_text(f"✅ {symbol} removed from watchlist")
            else:
                await update.message.reply_text(f"ℹ️ {symbol} not in watchlist")
        else:
            await update.message.reply_text("Usage: /watchlist add|remove SYMBOL")
    except Exception as exc:
        await update.message.reply_text(f"❌ Error: {exc}")
