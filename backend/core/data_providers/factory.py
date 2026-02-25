from .base import BaseDataProvider


def get_live_provider() -> BaseDataProvider:
    """Returns Alpaca provider for live prices, falls back to yfinance."""
    from .alpaca_provider import AlpacaProvider
    return AlpacaProvider()


def get_historical_provider() -> BaseDataProvider:
    """Returns yfinance provider for historical data and fundamentals."""
    from .yfinance_provider import YFinanceProvider
    return YFinanceProvider()
