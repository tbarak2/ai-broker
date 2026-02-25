import logging

from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.response import Response

from .models import AIRecommendation, StrategyConfig
from .serializers import AIRecommendationSerializer, StrategyConfigSerializer
from .services import AIAdvisorService

logger = logging.getLogger(__name__)


class AIRecommendationViewSet(viewsets.ReadOnlyModelViewSet):
    serializer_class = AIRecommendationSerializer

    def get_queryset(self):
        qs = AIRecommendation.objects.select_related("portfolio")
        portfolio_id = self.request.query_params.get("portfolio_id")
        rec_status = self.request.query_params.get("status")
        provider = self.request.query_params.get("provider")
        symbol = self.request.query_params.get("symbol")

        if portfolio_id:
            qs = qs.filter(portfolio_id=portfolio_id)
        if rec_status:
            qs = qs.filter(status=rec_status.upper())
        if provider:
            qs = qs.filter(provider=provider.upper())
        if symbol:
            qs = qs.filter(symbol=symbol.upper())
        return qs

    @action(detail=True, methods=["post"])
    def approve(self, request, pk=None):
        svc = AIAdvisorService()
        try:
            rec = svc.approve_recommendation(int(pk))
            return Response(AIRecommendationSerializer(rec).data)
        except ValueError as exc:
            return Response({"error": str(exc)}, status=status.HTTP_400_BAD_REQUEST)
        except Exception as exc:
            logger.exception("Approve recommendation failed: %s", exc)
            return Response({"error": str(exc)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

    @action(detail=True, methods=["post"])
    def reject(self, request, pk=None):
        svc = AIAdvisorService()
        try:
            rec = svc.reject_recommendation(int(pk))
            return Response(AIRecommendationSerializer(rec).data)
        except ValueError as exc:
            return Response({"error": str(exc)}, status=status.HTTP_400_BAD_REQUEST)

    @action(detail=False, methods=["post"])
    def run_analysis(self, request):
        portfolio_id = request.data.get("portfolio_id")
        if not portfolio_id:
            return Response(
                {"error": "portfolio_id is required"}, status=status.HTTP_400_BAD_REQUEST
            )
        from .tasks import run_ai_analysis
        run_ai_analysis.delay(portfolio_id)
        return Response({"status": "Analysis queued", "portfolio_id": portfolio_id})


class StrategyConfigViewSet(viewsets.ModelViewSet):
    serializer_class = StrategyConfigSerializer

    def get_queryset(self):
        qs = StrategyConfig.objects.select_related("portfolio")
        portfolio_id = self.request.query_params.get("portfolio_id")
        if portfolio_id:
            qs = qs.filter(portfolio_id=portfolio_id)
        return qs
