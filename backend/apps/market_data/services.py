"""
Market data service — coordinates data providers, caching, and DB persistence.
Price lookups go: Redis cache → live provider → fallback to DB.
"""
import logging
from decimal import Decimal
from typing import List, Optional

from django.conf import settings
from django.core.cache import cache
from django.utils import timezone

from core.data_providers.factory import get_live_provider, get_historical_provider
from core.data_providers.base import PriceData, FundamentalData

logger = logging.getLogger(__name__)

PRICE_CACHE_PREFIX = "price:"
PRICE_CACHE_TTL = getattr(settings, "PRICE_CACHE_TTL", 60)


class MarketDataService:
    def __init__(self):
        self._live = get_live_provider()
        self._historical = get_historical_provider()

    def get_current_price(self, symbol: str) -> Decimal:
        """
        Return current price (Decimal). Checks Redis cache first.
        Falls back to live provider, then DB last snapshot.
        """
        cache_key = f"{PRICE_CACHE_PREFIX}{symbol}"
        cached = cache.get(cache_key)
        if cached is not None:
            return Decimal(str(cached))

        try:
            price_data = self._live.get_current_price(symbol)
            price = price_data.price
            cache.set(cache_key, float(price), PRICE_CACHE_TTL)
            self._save_snapshot(symbol, price_data)
            return price
        except Exception as exc:
            logger.warning("Live price fetch failed for %s: %s — trying yfinance", symbol, exc)
            try:
                price_data = self._historical.get_current_price(symbol)
                price = price_data.price
                cache.set(cache_key, float(price), PRICE_CACHE_TTL)
                return price
            except Exception:
                return self._get_price_from_db(symbol)

    def get_price_data(self, symbol: str) -> PriceData:
        """Return full PriceData (price + change + volume etc.)."""
        cache_key = f"price_data:{symbol}"
        cached = cache.get(cache_key)
        if cached:
            return PriceData(**cached)
        try:
            price_data = self._live.get_current_price(symbol)
            cache.set(cache_key, {
                "symbol": price_data.symbol,
                "price": float(price_data.price),
                "change": float(price_data.change),
                "change_pct": price_data.change_pct,
                "volume": price_data.volume,
                "market_cap": price_data.market_cap,
                "timestamp": price_data.timestamp,
                "source": price_data.source,
            }, PRICE_CACHE_TTL)
            return price_data
        except Exception as exc:
            logger.warning("Price data fetch failed for %s: %s", symbol, exc)
            price = self._get_price_from_db(symbol)
            return PriceData(
                symbol=symbol,
                price=price,
                change=Decimal("0"),
                change_pct=0.0,
                volume=0,
            )

    def get_historical_ohlcv(self, symbol: str, period: str = "90d"):
        """Return DataFrame with OHLCV data."""
        try:
            return self._historical.get_historical_ohlcv(symbol, period)
        except Exception as exc:
            logger.error("Historical data fetch failed for %s: %s", symbol, exc)
            raise

    def get_fundamentals(self, symbol: str) -> FundamentalData:
        try:
            return self._historical.get_fundamentals(symbol)
        except Exception as exc:
            logger.warning("Fundamentals fetch failed for %s: %s", symbol, exc)
            return FundamentalData(symbol=symbol)

    def update_prices_for_symbols(self, symbols: List[str]) -> dict:
        """Bulk refresh prices for a list of symbols. Returns {symbol: price}."""
        price_map = {}
        for symbol in symbols:
            try:
                price = self.get_current_price(symbol)
                price_map[symbol] = price
            except Exception as exc:
                logger.warning("Failed to update price for %s: %s", symbol, exc)
        return price_map

    def get_news(self, symbol: str, limit: int = 10) -> list:
        """Return recent news items for a symbol from DB."""
        from .models import NewsItem
        return list(
            NewsItem.objects.filter(symbol=symbol).order_by("-published_at")[:limit]
        )

    def get_recent_snapshots(self, symbol: str, limit: int = 100):
        """Return recent PriceSnapshot records from DB."""
        from .models import PriceSnapshot
        return PriceSnapshot.objects.filter(symbol=symbol).order_by("-timestamp")[:limit]

    def _get_price_from_db(self, symbol: str) -> Decimal:
        from .models import PriceSnapshot
        snap = PriceSnapshot.objects.filter(symbol=symbol).order_by("-timestamp").first()
        if snap:
            return snap.close
        raise ValueError(f"No price data found for {symbol}")

    def _save_snapshot(self, symbol: str, price_data: PriceData) -> None:
        from .models import PriceSnapshot
        try:
            PriceSnapshot.objects.create(
                symbol=symbol,
                close=price_data.price,
                volume=price_data.volume or 0,
                timestamp=timezone.now(),
                source=PriceSnapshot.Source.ALPACA
                if price_data.source == "alpaca"
                else PriceSnapshot.Source.YFINANCE,
            )
        except Exception as exc:
            logger.debug("Could not save price snapshot for %s: %s", symbol, exc)
