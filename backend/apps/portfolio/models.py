from decimal import Decimal
from django.contrib.auth.models import User
from django.db import models


class Portfolio(models.Model):
    user = models.ForeignKey(
        User, on_delete=models.CASCADE, related_name="portfolios", null=True, blank=True
    )
    name = models.CharField(max_length=200)
    initial_capital = models.DecimalField(max_digits=15, decimal_places=2)
    cash_balance = models.DecimalField(max_digits=15, decimal_places=2)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["-created_at"]

    def __str__(self):
        return f"{self.name} (${self.cash_balance:.2f} cash)"

    @property
    def positions_value(self) -> Decimal:
        return sum(
            (p.quantity * p.current_price for p in self.positions.filter(quantity__gt=0)),
            Decimal("0"),
        )

    @property
    def total_value(self) -> Decimal:
        return self.cash_balance + self.positions_value

    @property
    def total_pnl(self) -> Decimal:
        return self.total_value - self.initial_capital

    @property
    def total_pnl_pct(self) -> float:
        if self.initial_capital == 0:
            return 0.0
        return float(self.total_pnl / self.initial_capital * 100)


class Position(models.Model):
    class AssetType(models.TextChoices):
        STOCK = "STOCK", "Stock"
        ETF = "ETF", "ETF"
        CRYPTO = "CRYPTO", "Crypto"
        OPTION = "OPTION", "Option"

    portfolio = models.ForeignKey(
        Portfolio, on_delete=models.CASCADE, related_name="positions"
    )
    symbol = models.CharField(max_length=20)
    asset_type = models.CharField(
        max_length=10, choices=AssetType.choices, default=AssetType.STOCK
    )
    quantity = models.DecimalField(max_digits=15, decimal_places=6, default=Decimal("0"))
    avg_cost_price = models.DecimalField(max_digits=15, decimal_places=6, default=Decimal("0"))
    current_price = models.DecimalField(max_digits=15, decimal_places=6, default=Decimal("0"))
    realized_pnl = models.DecimalField(max_digits=15, decimal_places=2, default=Decimal("0"))
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        unique_together = [("portfolio", "symbol")]
        ordering = ["symbol"]

    def __str__(self):
        return f"{self.symbol} x{self.quantity} in {self.portfolio.name}"

    @property
    def market_value(self) -> Decimal:
        return self.quantity * self.current_price

    @property
    def unrealized_pnl(self) -> Decimal:
        return (self.current_price - self.avg_cost_price) * self.quantity

    @property
    def unrealized_pnl_pct(self) -> float:
        if self.avg_cost_price == 0:
            return 0.0
        return float(
            (self.current_price - self.avg_cost_price) / self.avg_cost_price * 100
        )

    @property
    def weight_pct(self) -> float:
        portfolio_value = self.portfolio.total_value
        if portfolio_value == 0:
            return 0.0
        return float(self.market_value / portfolio_value * 100)
