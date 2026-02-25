"""
Django signals for cross-app event communication (Observer pattern).

Publishers fire signals; subscribers react independently.
This keeps apps decoupled — telegram_bot listens to portfolio/trading
events without portfolio/trading knowing about telegram_bot.
"""
from django.dispatch import Signal

# Fired when a new AI recommendation is created
# kwargs: recommendation (AIRecommendation instance)
recommendation_created = Signal()

# Fired when a trade is successfully executed
# kwargs: trade (Trade instance)
trade_executed = Signal()

# Fired when stop-loss triggers
# kwargs: position (Position instance), triggered_price (Decimal)
stop_loss_triggered = Signal()

# Fired when take-profit triggers
# kwargs: position (Position instance), triggered_price (Decimal)
take_profit_triggered = Signal()

# Fired when an order is approved (via UI or Telegram)
# kwargs: order (Order instance)
order_approved = Signal()

# Fired when portfolio balance is updated significantly (>5% change)
# kwargs: portfolio (Portfolio instance), change_pct (float)
portfolio_updated = Signal()
