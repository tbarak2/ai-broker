from django.contrib import admin
from django.urls import path, include

urlpatterns = [
    path("admin/", admin.site.urls),
    path("api/", include("apps.portfolio.urls")),
    path("api/", include("apps.trading.urls")),
    path("api/", include("apps.market_data.urls")),
    path("api/", include("apps.ai_advisor.urls")),
    path("api/", include("apps.analytics.urls")),
]
