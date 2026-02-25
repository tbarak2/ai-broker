from rest_framework import serializers
from .models import PriceSnapshot, NewsItem


class PriceSnapshotSerializer(serializers.ModelSerializer):
    class Meta:
        model = PriceSnapshot
        fields = [
            "id", "symbol", "asset_type", "open", "high", "low",
            "close", "volume", "timestamp", "source",
        ]


class NewsItemSerializer(serializers.ModelSerializer):
    class Meta:
        model = NewsItem
        fields = [
            "id", "symbol", "headline", "summary", "source_url",
            "author", "sentiment_score", "published_at",
        ]
