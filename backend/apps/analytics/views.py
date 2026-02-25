from rest_framework.decorators import api_view
from rest_framework.response import Response

from .services import AnalyticsService


@api_view(["GET"])
def pnl_history(request, portfolio_id):
    period = request.query_params.get("period", "30d")
    svc = AnalyticsService()
    data = svc.get_pnl_history(portfolio_id, period)
    return Response({"portfolio_id": portfolio_id, "period": period, "data": data})


@api_view(["GET"])
def portfolio_metrics(request, portfolio_id):
    svc = AnalyticsService()
    data = svc.get_portfolio_metrics(portfolio_id)
    return Response(data)
