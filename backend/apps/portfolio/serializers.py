from rest_framework import serializers
from .models import Portfolio, Position


class PositionSerializer(serializers.ModelSerializer):
    market_value = serializers.DecimalField(max_digits=15, decimal_places=2, read_only=True)
    unrealized_pnl = serializers.DecimalField(max_digits=15, decimal_places=2, read_only=True)
    unrealized_pnl_pct = serializers.FloatField(read_only=True)
    weight_pct = serializers.FloatField(read_only=True)

    class Meta:
        model = Position
        fields = [
            "id", "symbol", "asset_type", "quantity", "avg_cost_price",
            "current_price", "market_value", "unrealized_pnl", "unrealized_pnl_pct",
            "realized_pnl", "weight_pct",
        ]


class PortfolioSerializer(serializers.ModelSerializer):
    total_value = serializers.DecimalField(max_digits=15, decimal_places=2, read_only=True)
    total_pnl = serializers.DecimalField(max_digits=15, decimal_places=2, read_only=True)
    total_pnl_pct = serializers.FloatField(read_only=True)
    positions_count = serializers.SerializerMethodField()

    class Meta:
        model = Portfolio
        fields = [
            "id", "name", "initial_capital", "cash_balance",
            "total_value", "total_pnl", "total_pnl_pct",
            "positions_count", "created_at", "updated_at",
        ]
        read_only_fields = ["cash_balance", "created_at", "updated_at"]

    def get_positions_count(self, obj):
        return obj.positions.filter(quantity__gt=0).count()

    def create(self, validated_data):
        # Set cash_balance = initial_capital on creation
        validated_data["cash_balance"] = validated_data["initial_capital"]
        return super().create(validated_data)
