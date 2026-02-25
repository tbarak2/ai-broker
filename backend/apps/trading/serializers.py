from rest_framework import serializers
from .models import Order, Trade


class OrderSerializer(serializers.ModelSerializer):
    total_value = serializers.SerializerMethodField()

    class Meta:
        model = Order
        fields = [
            "id", "portfolio", "symbol", "asset_type", "side", "order_type",
            "quantity", "limit_price", "stop_price", "status", "source",
            "ai_recommendation", "executed_at", "executed_price",
            "rejection_reason", "total_value", "created_at", "updated_at",
        ]
        read_only_fields = [
            "status", "executed_at", "executed_price", "created_at", "updated_at",
        ]

    def get_total_value(self, obj):
        if obj.executed_price and obj.quantity:
            return float(obj.executed_price * obj.quantity)
        return None


class CreateOrderSerializer(serializers.Serializer):
    portfolio_id = serializers.IntegerField()
    symbol = serializers.CharField(max_length=20)
    side = serializers.ChoiceField(choices=["BUY", "SELL"])
    quantity = serializers.DecimalField(max_digits=15, decimal_places=6)
    order_type = serializers.ChoiceField(
        choices=["MARKET", "LIMIT", "STOP"], default="MARKET"
    )
    asset_type = serializers.ChoiceField(
        choices=["STOCK", "ETF", "CRYPTO", "OPTION"], default="STOCK"
    )
    limit_price = serializers.DecimalField(
        max_digits=15, decimal_places=6, required=False, allow_null=True
    )
    stop_price = serializers.DecimalField(
        max_digits=15, decimal_places=6, required=False, allow_null=True
    )


class TradeSerializer(serializers.ModelSerializer):
    total_value = serializers.DecimalField(
        max_digits=15, decimal_places=2, read_only=True
    )

    class Meta:
        model = Trade
        fields = [
            "id", "order", "portfolio", "symbol", "side", "quantity",
            "price", "commission", "portfolio_balance_after",
            "total_value", "executed_at",
        ]
        read_only_fields = fields
