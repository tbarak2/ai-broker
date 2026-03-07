from decimal import Decimal
from django.db import models
from apps.portfolio.models import Portfolio


class AIRecommendation(models.Model):
    class Provider(models.TextChoices):
        CLAUDE = "CLAUDE", "Claude"
        OPENAI = "OPENAI", "OpenAI"
        GEMINI = "GEMINI", "Gemini"

    class Action(models.TextChoices):
        BUY = "BUY", "Buy"
        SELL = "SELL", "Sell"
        HOLD = "HOLD", "Hold"
        REBALANCE = "REBALANCE", "Rebalance"

    class Status(models.TextChoices):
        PENDING = "PENDING", "Pending"
        APPROVED = "APPROVED", "Approved"
        REJECTED = "REJECTED", "Rejected"
        EXECUTED = "EXECUTED", "Executed"
        EXPIRED = "EXPIRED", "Expired"

    class AssetType(models.TextChoices):
        STOCK = "STOCK", "Stock"
        ETF = "ETF", "ETF"
        CRYPTO = "CRYPTO", "Crypto"
        OPTION = "OPTION", "Option"

    portfolio = models.ForeignKey(
        Portfolio, on_delete=models.CASCADE, related_name="recommendations"
    )
    provider = models.CharField(max_length=10, choices=Provider.choices)
    symbol = models.CharField(max_length=20)
    asset_type = models.CharField(
        max_length=10, choices=AssetType.choices, default=AssetType.STOCK
    )
    action = models.CharField(max_length=10, choices=Action.choices)
    confidence = models.DecimalField(
        max_digits=4, decimal_places=3, default=Decimal("0.500")
    )  # 0.000 to 1.000
    quantity_suggested = models.DecimalField(
        max_digits=15, decimal_places=6, default=Decimal("0")
    )
    price_target = models.DecimalField(
        max_digits=15, decimal_places=6, null=True, blank=True
    )
    stop_loss = models.DecimalField(
        max_digits=15, decimal_places=6, null=True, blank=True
    )
    take_profit = models.DecimalField(
        max_digits=15, decimal_places=6, null=True, blank=True
    )
    reasoning = models.TextField()
    analysis_data = models.JSONField(default=dict)  # serialized AnalysisContext
    status = models.CharField(
        max_length=10, choices=Status.choices, default=Status.PENDING
    )
    created_at = models.DateTimeField(auto_now_add=True)
    expires_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        ordering = ["-created_at"]
        indexes = [
            models.Index(fields=["portfolio", "status"]),
            models.Index(fields=["symbol", "created_at"]),
        ]

    def __str__(self):
        return (
            f"[{self.provider}] {self.action} {self.symbol} "
            f"({float(self.confidence)*100:.0f}%) [{self.status}]"
        )


class StrategyConfig(models.Model):
    class RiskTolerance(models.TextChoices):
        LOW = "LOW", "Low"
        MEDIUM = "MEDIUM", "Medium"
        HIGH = "HIGH", "High"

    portfolio = models.OneToOneField(
        Portfolio, on_delete=models.CASCADE, related_name="strategy_config"
    )
    ai_providers = models.JSONField(default=list)  # ["claude", "openai", "gemini"]
    strategies = models.JSONField(
        default=list
    )  # ["technical", "sentiment", "fundamental", "rebalancing"]
    risk_tolerance = models.CharField(
        max_length=6, choices=RiskTolerance.choices, default=RiskTolerance.MEDIUM
    )
    max_position_size_pct = models.DecimalField(
        max_digits=5, decimal_places=2, default=Decimal("10.00")
    )  # % of portfolio
    analysis_interval_minutes = models.IntegerField(default=30)
    watchlist = models.JSONField(default=list)  # ["AAPL", "TSLA", ...]
    is_active = models.BooleanField(default=True)
    auto_trade = models.BooleanField(
        default=False,
        help_text="When enabled, high-confidence AI recommendations are executed automatically.",
    )
    auto_trade_min_confidence = models.DecimalField(
        max_digits=4, decimal_places=3, default=Decimal("0.700"),
        help_text="Minimum confidence (0–1) required for auto-execution.",
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = "Strategy Config"

    def __str__(self):
        return f"{self.portfolio.name} strategy ({self.risk_tolerance})"
