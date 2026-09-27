from django.urls import path
from .views import RecommendationView, AlgorithmListView

urlpatterns = [
    path("recommendations/", RecommendationView.as_view(), name="recommendations"),
    path("algorithms/", AlgorithmListView.as_view(), name="algorithms"),
]
