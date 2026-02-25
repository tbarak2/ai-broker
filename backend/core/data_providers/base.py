from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from decimal import Decimal
from typing import Optional
import pandas as pd


@dataclass
class PriceData:
    symbol: str
    price: Decimal
    change: Decimal
    change_pct: float
    volume: int
    market_cap: Optional[int] = None
    timestamp: Optional[str] = None
    source: str = "unknown"


@dataclass
class FundamentalData:
    symbol: str
    pe_ratio: Optional[float] = None
    eps: Optional[float] = None
    market_cap: Optional[int] = None
    dividend_yield: Optional[float] = None
    sector: Optional[str] = None
    industry: Optional[str] = None


class BaseDataProvider(ABC):
    """
    Abstract market data provider (Strategy pattern).
    Implementations: AlpacaProvider (live), YFinanceProvider (historical).
    """

    @abstractmethod
    def get_current_price(self, symbol: str) -> PriceData:
        """Get the latest price for a symbol."""
        ...

    @abstractmethod
    def get_historical_ohlcv(
        self, symbol: str, period: str = "90d", interval: str = "1d"
    ) -> pd.DataFrame:
        """
        Get OHLCV historical data as a DataFrame.
        Columns: open, high, low, close, volume
        Index: DatetimeIndex
        """
        ...

    @abstractmethod
    def get_fundamentals(self, symbol: str) -> FundamentalData:
        """Get fundamental data (P/E, EPS, market cap, etc.)."""
        ...
