from rest_framework.routers import DefaultRouter
from .views import AIRecommendationViewSet, StrategyConfigViewSet

router = DefaultRouter()
router.register("recommendations", AIRecommendationViewSet, basename="recommendation")
router.register("strategy", StrategyConfigViewSet, basename="strategy")

urlpatterns = router.urls
