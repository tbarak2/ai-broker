"""
Telegram bot setup.
Run via: python manage.py run_telegram_bot
Uses polling in local dev, webhook in production.
"""
import logging
import re

from telegram.ext import Application, CommandHandler, MessageHandler, filters

logger = logging.getLogger(__name__)


def create_application(token: str):
    """Build and configure the Telegram Application."""
    from .handlers import (
        cmd_start,
        cmd_status,
        cmd_positions,
        cmd_pending,
        cmd_approve,
        cmd_reject,
        cmd_buy,
        cmd_sell,
        cmd_report,
        cmd_watchlist,
    )

    app = Application.builder().token(token).build()

    # Standard commands
    app.add_handler(CommandHandler("start", cmd_start))
    app.add_handler(CommandHandler("status", cmd_status))
    app.add_handler(CommandHandler("positions", cmd_positions))
    app.add_handler(CommandHandler("pending", cmd_pending))
    app.add_handler(CommandHandler("buy", cmd_buy))
    app.add_handler(CommandHandler("sell", cmd_sell))
    app.add_handler(CommandHandler("report", cmd_report))
    app.add_handler(CommandHandler("watchlist", cmd_watchlist))

    # Dynamic /approve_<id> and /reject_<id> handlers
    app.add_handler(
        MessageHandler(
            filters.Regex(re.compile(r"^/approve_\d+", re.IGNORECASE)),
            cmd_approve,
        )
    )
    app.add_handler(
        MessageHandler(
            filters.Regex(re.compile(r"^/reject_\d+", re.IGNORECASE)),
            cmd_reject,
        )
    )

    return app


def run_polling(token: str):
    """Start the bot in polling mode (local development)."""
    app = create_application(token)
    logger.info("Starting Telegram bot in polling mode...")
    app.run_polling(drop_pending_updates=True)
