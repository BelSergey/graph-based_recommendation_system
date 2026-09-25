from django.test import SimpleTestCase

from recommender.algorithms.collaborative import (
    CollaborativeGraphRecommender,
)
from recommender.algorithms.pagerank import PageRankRecommender
from recommender.registry import get_recommender_class


class AlgorithmRegistryTestCase(SimpleTestCase):
    def test_get_pagerank_class(self):
        self.assertIs(
            get_recommender_class("pagerank"),
            PageRankRecommender,
        )

    def test_get_collaborative_class(self):
        self.assertIs(
            get_recommender_class("collaborative"),
            CollaborativeGraphRecommender,
        )

    def test_unknown_algorithm_raises_error(self):
        with self.assertRaises(ValueError):
            get_recommender_class("unknown")
