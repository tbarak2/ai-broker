from .base import BaseDataProvider


def get_live_provider() -> BaseDataProvider:
    """Returns Alpaca provider for live prices, falls back to yfinance."""
    from .alpaca_provider import AlpacaProvider
    return AlpacaProvider()


def get_historical_provider() -> BaseDataProvider:
    """Returns Alpaca for historical OHLCV (yfinance as fallback for fundamentals)."""
    from .alpaca_provider import AlpacaProvider
    return AlpacaProvider()
