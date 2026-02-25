from decimal import Decimal
from django.db import models


class PriceSnapshot(models.Model):
    class AssetType(models.TextChoices):
        STOCK = "STOCK", "Stock"
        ETF = "ETF", "ETF"
        CRYPTO = "CRYPTO", "Crypto"
        OPTION = "OPTION", "Option"

    class Source(models.TextChoices):
        ALPACA = "ALPACA", "Alpaca"
        YFINANCE = "YFINANCE", "yFinance"

    symbol = models.CharField(max_length=20, db_index=True)
    asset_type = models.CharField(
        max_length=10, choices=AssetType.choices, default=AssetType.STOCK
    )
    open = models.DecimalField(max_digits=15, decimal_places=6, null=True, blank=True)
    high = models.DecimalField(max_digits=15, decimal_places=6, null=True, blank=True)
    low = models.DecimalField(max_digits=15, decimal_places=6, null=True, blank=True)
    close = models.DecimalField(max_digits=15, decimal_places=6)
    volume = models.BigIntegerField(null=True, blank=True)
    timestamp = models.DateTimeField(db_index=True)
    source = models.CharField(
        max_length=10, choices=Source.choices, default=Source.YFINANCE
    )

    class Meta:
        ordering = ["-timestamp"]
        indexes = [
            models.Index(fields=["symbol", "timestamp"]),
        ]

    def __str__(self):
        return f"{self.symbol} @ ${self.close} ({self.timestamp:%Y-%m-%d %H:%M})"


class NewsItem(models.Model):
    symbol = models.CharField(max_length=20, db_index=True)
    headline = models.TextField()
    summary = models.TextField(blank=True)
    source_url = models.URLField(max_length=500, blank=True)
    author = models.CharField(max_length=200, blank=True)
    sentiment_score = models.DecimalField(
        max_digits=5, decimal_places=4, null=True, blank=True
    )  # -1.0 to 1.0
    published_at = models.DateTimeField(db_index=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["-published_at"]
        indexes = [
            models.Index(fields=["symbol", "published_at"]),
        ]

    def __str__(self):
        return f"[{self.symbol}] {self.headline[:80]}"
