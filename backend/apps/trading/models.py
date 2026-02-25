from decimal import Decimal
from django.db import models
from apps.portfolio.models import Portfolio


class Order(models.Model):
    class Side(models.TextChoices):
        BUY = "BUY", "Buy"
        SELL = "SELL", "Sell"

    class OrderType(models.TextChoices):
        MARKET = "MARKET", "Market"
        LIMIT = "LIMIT", "Limit"
        STOP = "STOP", "Stop"

    class Status(models.TextChoices):
        PENDING_APPROVAL = "PENDING_APPROVAL", "Pending Approval"
        APPROVED = "APPROVED", "Approved"
        REJECTED = "REJECTED", "Rejected"
        EXECUTED = "EXECUTED", "Executed"
        CANCELLED = "CANCELLED", "Cancelled"
        FAILED = "FAILED", "Failed"

    class Source(models.TextChoices):
        AI_SUGGESTED = "AI_SUGGESTED", "AI Suggested"
        MANUAL = "MANUAL", "Manual"

    class AssetType(models.TextChoices):
        STOCK = "STOCK", "Stock"
        ETF = "ETF", "ETF"
        CRYPTO = "CRYPTO", "Crypto"
        OPTION = "OPTION", "Option"

    portfolio = models.ForeignKey(
        Portfolio, on_delete=models.CASCADE, related_name="orders"
    )
    symbol = models.CharField(max_length=20)
    asset_type = models.CharField(
        max_length=10, choices=AssetType.choices, default=AssetType.STOCK
    )
    side = models.CharField(max_length=4, choices=Side.choices)
    order_type = models.CharField(
        max_length=6, choices=OrderType.choices, default=OrderType.MARKET
    )
    quantity = models.DecimalField(max_digits=15, decimal_places=6)
    limit_price = models.DecimalField(
        max_digits=15, decimal_places=6, null=True, blank=True
    )
    stop_price = models.DecimalField(
        max_digits=15, decimal_places=6, null=True, blank=True
    )
    status = models.CharField(
        max_length=20, choices=Status.choices, default=Status.PENDING_APPROVAL
    )
    source = models.CharField(
        max_length=12, choices=Source.choices, default=Source.MANUAL
    )
    # FK to AIRecommendation set via string to avoid circular import
    ai_recommendation = models.ForeignKey(
        "ai_advisor.AIRecommendation",
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="orders",
    )
    executed_at = models.DateTimeField(null=True, blank=True)
    executed_price = models.DecimalField(
        max_digits=15, decimal_places=6, null=True, blank=True
    )
    rejection_reason = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["-created_at"]

    def __str__(self):
        return f"{self.side} {self.quantity} {self.symbol} [{self.status}]"


class Trade(models.Model):
    """Immutable ledger record created after an order is executed."""

    class Side(models.TextChoices):
        BUY = "BUY", "Buy"
        SELL = "SELL", "Sell"

    order = models.OneToOneField(Order, on_delete=models.CASCADE, related_name="trade")
    portfolio = models.ForeignKey(
        Portfolio, on_delete=models.CASCADE, related_name="trades"
    )
    symbol = models.CharField(max_length=20)
    side = models.CharField(max_length=4, choices=Side.choices)
    quantity = models.DecimalField(max_digits=15, decimal_places=6)
    price = models.DecimalField(max_digits=15, decimal_places=6)
    commission = models.DecimalField(
        max_digits=10, decimal_places=2, default=Decimal("0.00")
    )
    portfolio_balance_after = models.DecimalField(max_digits=15, decimal_places=2)
    executed_at = models.DateTimeField()

    class Meta:
        ordering = ["-executed_at"]

    def __str__(self):
        return f"{self.side} {self.quantity} {self.symbol} @ ${self.price}"

    @property
    def total_value(self) -> Decimal:
        return self.quantity * self.price
