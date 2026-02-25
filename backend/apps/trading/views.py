import logging
from decimal import Decimal

from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.response import Response

from .models import Order, Trade
from .serializers import OrderSerializer, CreateOrderSerializer, TradeSerializer
from .services import TradingService

logger = logging.getLogger(__name__)


class OrderViewSet(viewsets.ReadOnlyModelViewSet):
    serializer_class = OrderSerializer

    def get_queryset(self):
        qs = Order.objects.select_related("portfolio", "ai_recommendation")
        portfolio_id = self.request.query_params.get("portfolio_id")
        status_filter = self.request.query_params.get("status")
        if portfolio_id:
            qs = qs.filter(portfolio_id=portfolio_id)
        if status_filter:
            qs = qs.filter(status=status_filter)
        return qs

    def create(self, request):
        ser = CreateOrderSerializer(data=request.data)
        ser.is_valid(raise_exception=True)
        d = ser.validated_data

        svc = TradingService()
        order = svc.create_manual_order(
            portfolio_id=d["portfolio_id"],
            symbol=d["symbol"].upper(),
            side=d["side"],
            quantity=d["quantity"],
            order_type=d.get("order_type", "MARKET"),
            asset_type=d.get("asset_type", "STOCK"),
            limit_price=d.get("limit_price"),
            stop_price=d.get("stop_price"),
        )
        return Response(OrderSerializer(order).data, status=status.HTTP_201_CREATED)

    @action(detail=True, methods=["post"])
    def approve(self, request, pk=None):
        svc = TradingService()
        try:
            order = svc.approve_order(int(pk))
            return Response(OrderSerializer(order).data)
        except ValueError as exc:
            return Response({"error": str(exc)}, status=status.HTTP_400_BAD_REQUEST)

    @action(detail=True, methods=["post"])
    def reject(self, request, pk=None):
        reason = request.data.get("reason", "")
        svc = TradingService()
        try:
            order = svc.reject_order(int(pk), reason)
            return Response(OrderSerializer(order).data)
        except ValueError as exc:
            return Response({"error": str(exc)}, status=status.HTTP_400_BAD_REQUEST)

    @action(detail=True, methods=["post"])
    def cancel(self, request, pk=None):
        svc = TradingService()
        try:
            order = svc.cancel_order(int(pk))
            return Response(OrderSerializer(order).data)
        except ValueError as exc:
            return Response({"error": str(exc)}, status=status.HTTP_400_BAD_REQUEST)


class TradeViewSet(viewsets.ReadOnlyModelViewSet):
    serializer_class = TradeSerializer

    def get_queryset(self):
        qs = Trade.objects.select_related("order", "portfolio")
        portfolio_id = self.request.query_params.get("portfolio_id")
        if portfolio_id:
            qs = qs.filter(portfolio_id=portfolio_id)
        return qs
