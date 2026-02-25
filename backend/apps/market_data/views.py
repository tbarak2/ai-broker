from rest_framework import viewsets
from rest_framework.decorators import api_view
from rest_framework.response import Response

from .models import PriceSnapshot, NewsItem
from .serializers import PriceSnapshotSerializer, NewsItemSerializer
from .services import MarketDataService


class PriceSnapshotViewSet(viewsets.ReadOnlyModelViewSet):
    serializer_class = PriceSnapshotSerializer

    def get_queryset(self):
        qs = PriceSnapshot.objects.all()
        symbol = self.request.query_params.get("symbol")
        if symbol:
            qs = qs.filter(symbol=symbol.upper())
        return qs[:200]


class NewsItemViewSet(viewsets.ReadOnlyModelViewSet):
    serializer_class = NewsItemSerializer

    def get_queryset(self):
        qs = NewsItem.objects.all()
        symbol = self.request.query_params.get("symbol")
        if symbol:
            qs = qs.filter(symbol=symbol.upper())
        return qs[:50]


@api_view(["GET"])
def quote(request, symbol):
    """Real-time quote for a single symbol."""
    svc = MarketDataService()
    try:
        price_data = svc.get_price_data(symbol.upper())
        return Response({
            "symbol": price_data.symbol,
            "price": float(price_data.price),
            "change": float(price_data.change),
            "change_pct": price_data.change_pct,
            "volume": price_data.volume,
            "market_cap": price_data.market_cap,
            "timestamp": price_data.timestamp,
            "source": price_data.source,
        })
    except Exception as exc:
        return Response({"error": str(exc)}, status=503)


@api_view(["GET"])
def history(request, symbol):
    """OHLCV history for a symbol. Query param: period (default 90d)."""
    period = request.query_params.get("period", "90d")
    svc = MarketDataService()
    try:
        df = svc.get_historical_ohlcv(symbol.upper(), period)
        records = df.reset_index().rename(columns={"index": "date"}).to_dict("records")
        # Convert Timestamps to strings
        for r in records:
            if hasattr(r.get("date"), "isoformat"):
                r["date"] = r["date"].isoformat()
        return Response({"symbol": symbol.upper(), "period": period, "data": records})
    except Exception as exc:
        return Response({"error": str(exc)}, status=503)
