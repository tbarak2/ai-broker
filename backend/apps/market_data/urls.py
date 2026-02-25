from django.urls import path
from rest_framework.routers import DefaultRouter
from .views import PriceSnapshotViewSet, NewsItemViewSet, quote, history

router = DefaultRouter()
router.register("market/snapshots", PriceSnapshotViewSet, basename="snapshot")
router.register("market/news", NewsItemViewSet, basename="news")

urlpatterns = [
    path("market/quote/<str:symbol>/", quote, name="market-quote"),
    path("market/history/<str:symbol>/", history, name="market-history"),
] + router.urls
