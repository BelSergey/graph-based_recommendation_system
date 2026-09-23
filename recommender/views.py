from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from catalog.models import Product
from recommender.models import RecommendationModel, RecommendationResult
from recommender.serializers import AlgorithmSerializer


class RecommendationView(APIView):

    def get(self, request):
        user_id = request.query_params.get('user_id')
        algorithm = request.query_params.get('algorithm')
        top_k = int(request.query_params.get('top_k', 10))

        if not user_id:
            return Response({'error': 'user_id is required'}, status=status.HTTP_400_BAD_REQUEST)

        model_qs = RecommendationModel.objects.filter(algorithm=algorithm) if algorithm \
            else RecommendationModel.objects.filter(is_active=True)
        model_record = model_qs.order_by('-trained_at').first()

        if not model_record:
            return Response({'error': 'No trained model found'}, status=status.HTTP_404_NOT_FOUND)

        results = RecommendationResult.objects.filter(
            user_id=user_id, model=model_record
        ).select_related('product')[:top_k]

        data = [
            {
                'product': {
                    'id': r.product.id,
                    'title': r.product.title,
                    'price': r.product.price,
                },
                'score': r.score,
            }
            for r in results
        ]
        return Response({
            'algorithm': model_record.algorithm,
            'version': model_record.version,
            'results': data,
        })


class AlgorithmListView(APIView):
    """GET /api/algorithms/ — список доступных обученных моделей."""

    def get(self, request):
        models_qs = RecommendationModel.objects.all().order_by('algorithm', '-trained_at')
        serializer = AlgorithmSerializer(models_qs, many=True)
        return Response(serializer.data)