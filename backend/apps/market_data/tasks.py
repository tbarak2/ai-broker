"""Celery tasks for market data fetching."""
import logging

from celery import shared_task

logger = logging.getLogger(__name__)


def _get_all_watchlist_symbols() -> list[str]:
    """Collect symbols from all active StrategyConfigs."""
    try:
        from apps.ai_advisor.models import StrategyConfig
        symbols = set()
        for config in StrategyConfig.objects.all():
            symbols.update(config.watchlist or [])
        return list(symbols)
    except Exception:
        return []


@shared_task(name="market_data.fetch_market_prices")
def fetch_market_prices():
    """Refresh prices for all symbols in all strategy watchlists."""
    from .services import MarketDataService
    from apps.portfolio.repositories import PortfolioRepository

    symbols = _get_all_watchlist_symbols()

    # Also include symbols in open positions
    try:
        from apps.portfolio.models import Position
        position_symbols = list(
            Position.objects.filter(quantity__gt=0)
            .values_list("symbol", flat=True)
            .distinct()
        )
        symbols = list(set(symbols + position_symbols))
    except Exception:
        pass

    if not symbols:
        logger.info("No symbols to fetch prices for")
        return {"updated": 0}

    svc = MarketDataService()
    price_map = svc.update_prices_for_symbols(symbols)

    # Update position current prices
    try:
        from apps.portfolio.repositories import PortfolioRepository
        repo = PortfolioRepository()
        from decimal import Decimal
        repo.update_current_prices({s: p for s, p in price_map.items()})
    except Exception as exc:
        logger.warning("Failed to update position prices: %s", exc)

    logger.info("Updated prices for %d symbols", len(price_map))
    return {"updated": len(price_map), "symbols": list(price_map.keys())}


@shared_task(name="market_data.fetch_news")
def fetch_news():
    """
    Fetch recent news for all watched symbols via Alpha Vantage.
    Stores NewsItem records, computes simple sentiment.
    """
    from django.conf import settings
    import requests
    from django.utils import timezone
    from datetime import datetime
    from .models import NewsItem

    api_key = settings.ALPHA_VANTAGE_API_KEY
    if not api_key:
        logger.info("ALPHA_VANTAGE_API_KEY not set — skipping news fetch")
        return {"fetched": 0}

    symbols = _get_all_watchlist_symbols()
    total = 0

    for symbol in symbols[:5]:  # Alpha Vantage free tier is rate-limited
        try:
            url = (
                f"https://www.alphavantage.co/query"
                f"?function=NEWS_SENTIMENT&tickers={symbol}&limit=10&apikey={api_key}"
            )
            resp = requests.get(url, timeout=10)
            resp.raise_for_status()
            data = resp.json()
            feed = data.get("feed", [])

            for item in feed:
                pub_str = item.get("time_published", "")
                try:
                    pub_dt = datetime.strptime(pub_str, "%Y%m%dT%H%M%S")
                    pub_dt = timezone.make_aware(pub_dt)
                except ValueError:
                    pub_dt = timezone.now()

                # Get sentiment for this specific ticker
                sentiment = None
                for ticker_info in item.get("ticker_sentiment", []):
                    if ticker_info.get("ticker") == symbol:
                        try:
                            sentiment = float(ticker_info.get("ticker_sentiment_score", 0))
                        except (ValueError, TypeError):
                            pass
                        break

                NewsItem.objects.get_or_create(
                    symbol=symbol,
                    headline=item.get("title", "")[:500],
                    published_at=pub_dt,
                    defaults={
                        "summary": item.get("summary", "")[:2000],
                        "source_url": item.get("url", "")[:500],
                        "author": item.get("authors", [""])[0][:200] if item.get("authors") else "",
                        "sentiment_score": sentiment,
                    },
                )
                total += 1
        except Exception as exc:
            logger.warning("News fetch failed for %s: %s", symbol, exc)

    return {"fetched": total}
