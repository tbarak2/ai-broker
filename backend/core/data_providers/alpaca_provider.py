import logging
from decimal import Decimal
from typing import Optional

import pandas as pd
from django.conf import settings

from .base import BaseDataProvider, FundamentalData, PriceData

logger = logging.getLogger(__name__)


class AlpacaProvider(BaseDataProvider):
    """
    Live market data via Alpaca Markets API.
    Used for current prices and recent bars.
    Free tier supports US stocks and crypto.
    """

    def __init__(self):
        from alpaca.data.historical import StockHistoricalDataClient, CryptoHistoricalDataClient
        from alpaca.data.live import StockDataStream
        self._stock_client = StockHistoricalDataClient(
            api_key=settings.ALPACA_API_KEY,
            secret_key=settings.ALPACA_SECRET_KEY,
        )
        self._crypto_client = CryptoHistoricalDataClient(
            api_key=settings.ALPACA_API_KEY,
            secret_key=settings.ALPACA_SECRET_KEY,
        )

    def get_current_price(self, symbol: str) -> PriceData:
        from alpaca.data.requests import StockLatestQuoteRequest, CryptoLatestQuoteRequest

        try:
            is_crypto = "-USD" in symbol or "-USDT" in symbol
            if is_crypto:
                request = CryptoLatestQuoteRequest(symbol_or_symbols=symbol)
                quote = self._crypto_client.get_crypto_latest_quote(request)
            else:
                request = StockLatestQuoteRequest(symbol_or_symbols=symbol)
                quote = self._stock_client.get_stock_latest_quote(request)

            q = quote[symbol]
            mid_price = Decimal(str((q.ask_price + q.bid_price) / 2))
            return PriceData(
                symbol=symbol,
                price=mid_price,
                change=Decimal("0"),
                change_pct=0.0,
                volume=0,
                source="alpaca",
            )
        except Exception as exc:
            logger.warning("Alpaca price fetch failed for %s: %s. Falling back to yfinance.", symbol, exc)
            from .yfinance_provider import YFinanceProvider
            return YFinanceProvider().get_current_price(symbol)

    def get_historical_ohlcv(self, symbol: str, period: str = "90d", interval: str = "1d") -> pd.DataFrame:
        from alpaca.data.requests import StockBarsRequest
        from alpaca.data.timeframe import TimeFrame
        from datetime import datetime, timedelta

        days_map = {"7d": 7, "30d": 30, "90d": 90, "1y": 365}
        days = days_map.get(period, 90)
        end = datetime.now()
        start = end - timedelta(days=days)

        timeframe_map = {"1h": TimeFrame.Hour, "1d": TimeFrame.Day, "1w": TimeFrame.Week}
        timeframe = timeframe_map.get(interval, TimeFrame.Day)

        try:
            request = StockBarsRequest(
                symbol_or_symbols=symbol,
                timeframe=timeframe,
                start=start,
                end=end,
            )
            bars = self._stock_client.get_stock_bars(request)
            df = bars.df
            if symbol in df.index.get_level_values(0):
                df = df.loc[symbol]
            df.columns = [c.lower() for c in df.columns]
            return df[["open", "high", "low", "close", "volume"]]
        except Exception as exc:
            logger.warning("Alpaca historical failed for %s: %s. Falling back.", symbol, exc)
            from .yfinance_provider import YFinanceProvider
            return YFinanceProvider().get_historical_ohlcv(symbol, period, interval)

    def get_fundamentals(self, symbol: str) -> FundamentalData:
        # Alpaca doesn't provide fundamentals — delegate to yfinance
        from .yfinance_provider import YFinanceProvider
        return YFinanceProvider().get_fundamentals(symbol)
