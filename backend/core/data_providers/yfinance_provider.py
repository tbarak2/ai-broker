import logging
from decimal import Decimal

import pandas as pd
import yfinance as yf

from .base import BaseDataProvider, FundamentalData, PriceData

logger = logging.getLogger(__name__)


class YFinanceProvider(BaseDataProvider):
    """
    Historical market data via yfinance (Yahoo Finance).
    Used for:
    - Historical OHLCV for technical indicator computation
    - Fundamental data (P/E, EPS, market cap)
    - Fallback when Alpaca is unavailable
    """

    def get_current_price(self, symbol: str) -> PriceData:
        try:
            ticker = yf.Ticker(symbol)
            info = ticker.fast_info
            price = Decimal(str(info.last_price or 0))
            prev_close = Decimal(str(info.previous_close or price))
            change = price - prev_close
            change_pct = float(change / prev_close * 100) if prev_close else 0.0
            return PriceData(
                symbol=symbol,
                price=price,
                change=change,
                change_pct=round(change_pct, 2),
                volume=int(info.three_month_average_volume or 0),
                source="yfinance",
            )
        except Exception as exc:
            logger.error("yfinance price fetch failed for %s: %s", symbol, exc)
            raise

    def get_historical_ohlcv(
        self, symbol: str, period: str = "90d", interval: str = "1d"
    ) -> pd.DataFrame:
        # yfinance uses period directly: 7d, 30d, 3mo, 6mo, 1y
        period_map = {"90d": "3mo", "30d": "1mo", "7d": "5d", "1y": "1y"}
        yf_period = period_map.get(period, period)

        try:
            ticker = yf.Ticker(symbol)
            df = ticker.history(period=yf_period, interval=interval)
            df.columns = [c.lower() for c in df.columns]
            df = df[["open", "high", "low", "close", "volume"]]
            df.index = pd.to_datetime(df.index)
            df.index = df.index.tz_localize(None) if df.index.tz else df.index
            return df.dropna()
        except Exception as exc:
            logger.error("yfinance historical failed for %s: %s", symbol, exc)
            raise

    def get_fundamentals(self, symbol: str) -> FundamentalData:
        try:
            ticker = yf.Ticker(symbol)
            info = ticker.info
            return FundamentalData(
                symbol=symbol,
                pe_ratio=info.get("trailingPE"),
                eps=info.get("trailingEps"),
                market_cap=info.get("marketCap"),
                dividend_yield=info.get("dividendYield"),
                sector=info.get("sector"),
                industry=info.get("industry"),
            )
        except Exception as exc:
            logger.warning("yfinance fundamentals failed for %s: %s", symbol, exc)
            return FundamentalData(symbol=symbol)
