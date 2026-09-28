from decimal import Decimal

from django.test import TestCase
from django.db import IntegrityError

from catalog.models import Category, Product
from recommender.models import (
    RecommendationModel,
    RecommendationResult,
)
from users.models import User


class RecommendationModelTestCase(TestCase):
    def test_model_creation(self):
        model = RecommendationModel.objects.create(
            algorithm="pagerank",
            version="latest",
            file_path="storage/models/pagerank.pkl",
            metrics={"precision@10": 0.12},
            is_active=True,
        )

        self.assertEqual(str(model), "pagerank vlatest")
        self.assertEqual(model.algorithm, "pagerank")
        self.assertTrue(model.is_active)
        self.assertEqual(
            model.metrics["precision@10"],
            0.12,
        )

    def test_algorithm_and_version_are_unique(self):
        RecommendationModel.objects.create(
            algorithm="pagerank",
            version="latest",
            file_path="pagerank.pkl",
        )

        with self.assertRaises(Exception):
            RecommendationModel.objects.create(
                algorithm="pagerank",
                version="latest",
                file_path="other.pkl",
            )


class RecommendationResultTestCase(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(username="testuser")

        self.category = Category.objects.create(name="Электроника")

        self.product = Product.objects.create(
            title="Смартфон",
            category=self.category,
            price=Decimal("29999.00"),
        )

        self.model = RecommendationModel.objects.create(
            algorithm="pagerank",
            version="latest",
            file_path="pagerank.pkl",
            is_active=True,
        )

    def test_result_creation(self):
        result = RecommendationResult.objects.create(
            user=self.user,
            model=self.model,
            product=self.product,
            score=0.95,
        )

        self.assertEqual(result.user, self.user)
        self.assertEqual(result.model, self.model)
        self.assertEqual(result.product, self.product)
        self.assertEqual(result.score, 0.95)

    def test_results_are_ordered_by_score_descending(self):
        product_2 = Product.objects.create(
            title="Ноутбук",
            category=self.category,
            price=Decimal("79999.00"),
        )

        RecommendationResult.objects.create(
            user=self.user,
            model=self.model,
            product=self.product,
            score=0.50,
        )

        RecommendationResult.objects.create(
            user=self.user,
            model=self.model,
            product=product_2,
            score=0.90,
        )

        results = list(RecommendationResult.objects.all())

        self.assertEqual(results[0].score, 0.90)
        self.assertEqual(results[1].score, 0.50)

    def test_recommendation_result_is_unique(self):
        RecommendationResult.objects.create(
            user=self.user,
            model=self.model,
            product=self.product,
            score=0.95,
        )
        with self.assertRaises(IntegrityError):
            RecommendationResult.objects.create(
                user=self.user,
                model=self.model,
                product=self.product,
                score=0.80,
            )

    def test_only_one_active_model_per_algorithm(self):
        with self.assertRaises(IntegrityError):
            RecommendationModel.objects.create(
                algorithm="pagerank",
                version="v2",
                file_path="y",
                is_active=True,
            )
