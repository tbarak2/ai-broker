from rest_framework import serializers
from .models import AIRecommendation, StrategyConfig


class AIRecommendationSerializer(serializers.ModelSerializer):
    confidence_pct = serializers.SerializerMethodField()

    class Meta:
        model = AIRecommendation
        fields = [
            "id", "portfolio", "provider", "symbol", "asset_type",
            "action", "confidence", "confidence_pct", "quantity_suggested",
            "price_target", "stop_loss", "take_profit", "reasoning",
            "status", "created_at", "expires_at",
        ]
        read_only_fields = fields

    def get_confidence_pct(self, obj):
        return round(float(obj.confidence) * 100, 1)


class StrategyConfigSerializer(serializers.ModelSerializer):
    class Meta:
        model = StrategyConfig
        fields = [
            "id", "portfolio", "ai_providers", "strategies",
            "risk_tolerance", "max_position_size_pct",
            "analysis_interval_minutes", "watchlist", "is_active",
            "auto_trade", "auto_trade_min_confidence",
            "created_at", "updated_at",
        ]
        read_only_fields = ["id", "created_at", "updated_at"]
