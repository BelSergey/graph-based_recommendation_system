from rest_framework import serializers
from catalog.models import Product
from recommender.models import RecommendationModel


class ProductSerializer(serializers.ModelSerializer):
    class Meta:
        model = Product
        fields = ["id", "title", "category", "price"]


class RecommendationItemSerializer(serializers.Serializer):
    product = ProductSerializer()
    score = serializers.FloatField()


class AlgorithmSerializer(serializers.ModelSerializer):
    class Meta:
        model = RecommendationModel
        fields = ["algorithm", "version", "trained_at", "metrics", "is_active"]


class RecommendationQuerySerializer(serializers.Serializer):
    user_id = serializers.IntegerField(required=True, min_value=1)
    top_k = serializers.IntegerField(required=False, default=10, min_value=1, max_value=100)
