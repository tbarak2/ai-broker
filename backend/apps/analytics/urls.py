from django.urls import path
from .views import pnl_history, portfolio_metrics

urlpatterns = [
    path("analytics/<int:portfolio_id>/pnl/", pnl_history, name="analytics-pnl"),
    path(
        "analytics/<int:portfolio_id>/metrics/",
        portfolio_metrics,
        name="analytics-metrics",
    ),
]
