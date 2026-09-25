from decimal import Decimal

from django.urls import reverse
from rest_framework import status
from rest_framework.test import APITestCase

from catalog.models import Category, Product
from recommender.models import RecommendationModel, RecommendationResult
from users.models import User


class RecommendationAPITestCase(APITestCase):
    def setUp(self):
        self.category = Category.objects.create(
            name="Электроника"
        )

        self.product_1 = Product.objects.create(
            title="Смартфон",
            category=self.category,
            price=Decimal("29999.00"),
        )

        self.product_2 = Product.objects.create(
            title="Ноутбук",
            category=self.category,
            price=Decimal("79999.00"),
        )

        self.user = User.objects.create_user(
            username="testuser",
            password="password123",
        )

        self.model_record = RecommendationModel.objects.create(
            algorithm="pagerank",
            version="1",
            file_path="storage/models/pagerank_v1.pkl",
            is_active=True,
        )

        RecommendationResult.objects.create(
            user=self.user,
            model=self.model_record,
            product=self.product_1,
            score=0.95,
        )

        RecommendationResult.objects.create(
            user=self.user,
            model=self.model_record,
            product=self.product_2,
            score=0.80,
        )

    def test_get_recommendations(self):
        url = reverse("recommendations")

        response = self.client.get(
            url,
            {
                "user_id": self.user.id,
                "top_k": 10,
            },
        )

        self.assertEqual(
            response.status_code,
            status.HTTP_200_OK,
        )

        self.assertEqual(
            response.data["algorithm"],
            "pagerank",
        )

        self.assertEqual(
            response.data["version"],
            "1",
        )

        self.assertEqual(
            len(response.data["results"]),
            2,
        )

    def test_top_k_limits_results(self):
        url = reverse("recommendations")

        response = self.client.get(
            url,
            {
                "user_id": self.user.id,
                "top_k": 1,
            },
        )

        self.assertEqual(
            response.status_code,
            status.HTTP_200_OK,
        )

        self.assertEqual(
            len(response.data["results"]),
            1,
        )

    def test_missing_user_id_returns_400(self):
        url = reverse("recommendations")

        response = self.client.get(url)

        self.assertEqual(
            response.status_code,
            status.HTTP_400_BAD_REQUEST,
        )

    def test_invalid_top_k_returns_400(self):
        url = reverse("recommendations")

        response = self.client.get(
            url,
            {
                "user_id": self.user.id,
                "top_k": 101,
            },
        )

        self.assertEqual(
            response.status_code,
            status.HTTP_400_BAD_REQUEST,
        )

    def test_zero_user_id_returns_400(self):
        url = reverse("recommendations")

        response = self.client.get(
            url,
            {
                "user_id": 0,
            },
        )

        self.assertEqual(
            response.status_code,
            status.HTTP_400_BAD_REQUEST,
        )

    def test_unknown_user_can_return_empty_results(self):
        url = reverse("recommendations")

        response = self.client.get(
            url,
            {
                "user_id": 999999,
            },
        )

        self.assertEqual(
            response.status_code,
            status.HTTP_200_OK,
        )

        self.assertEqual(
            response.data["results"],
            [],
        )

    def test_unknown_algorithm_returns_404(self):
        url = reverse("recommendations")

        response = self.client.get(
            url,
            {
                "user_id": self.user.id,
                "algorithm": "unknown",
            },
        )

        self.assertEqual(
            response.status_code,
            status.HTTP_404_NOT_FOUND,
        )


class AlgorithmListAPITestCase(APITestCase):
    def setUp(self):
        self.category = Category.objects.create(
            name="Электроника"
        )

        self.user = User.objects.create_user(
            username="testuser",
            password="password123",
        )

        self.model_record = RecommendationModel.objects.create(
            algorithm="pagerank",
            version="latest",
            file_path="storage/models/pagerank_vlatest.pkl",
            metrics={
                "precision@10": 0.122,
                "recall@10": 0.0808,
                "ndcg@10": 0.1428,
            },
            is_active=True,
        )

    def test_get_algorithms_list(self):
        url = reverse("algorithms")

        response = self.client.get(url)

        self.assertEqual(
            response.status_code,
            status.HTTP_200_OK,
        )

        self.assertEqual(len(response.data), 1)

        item = response.data[0]

        self.assertEqual(item["algorithm"], "pagerank")
        self.assertEqual(item["version"], "latest")
        self.assertTrue(item["is_active"])
        self.assertEqual(
            item["metrics"]["precision@10"],
            0.122,
        )
