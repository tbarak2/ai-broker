from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.response import Response

from .models import Portfolio, Position
from .serializers import PortfolioSerializer, PositionSerializer


class PortfolioViewSet(viewsets.ModelViewSet):
    queryset = Portfolio.objects.all()
    serializer_class = PortfolioSerializer
    http_method_names = ["get", "post", "patch", "delete"]

    @action(detail=True, methods=["get"])
    def positions(self, request, pk=None):
        portfolio = self.get_object()
        positions = portfolio.positions.filter(quantity__gt=0)
        serializer = PositionSerializer(positions, many=True)
        return Response(serializer.data)

    @action(detail=True, methods=["get"])
    def pnl(self, request, pk=None):
        from apps.analytics.services import AnalyticsService
        portfolio = self.get_object()
        period = request.query_params.get("period", "30d")
        data = AnalyticsService().get_pnl_history(portfolio.id, period)
        return Response({"period": period, "data": data})

    @action(detail=True, methods=["get"])
    def metrics(self, request, pk=None):
        from apps.analytics.services import AnalyticsService
        portfolio = self.get_object()
        data = AnalyticsService().get_portfolio_metrics(portfolio.id)
        return Response(data)
