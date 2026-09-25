
import networkx as nx
from django.test import SimpleTestCase

from recommender.algorithms.collaborative import (
    CollaborativeGraphRecommender,
)


def build_test_graph():
    """
    Пользователь 1 смотрит товар 10.

    Пользователь 2 смотрит товары 10 и 20.
    Поэтому товар 20 должен быть кандидатом
    для пользователя 1.

    Пользователь 3 изолирован и смотрит товар 30.
    """
    graph = nx.Graph()

    graph.add_edge("u_1", "p_10", weight=5.0)

    graph.add_edge("u_2", "p_10", weight=5.0)
    graph.add_edge("u_2", "p_20", weight=5.0)

    graph.add_edge("u_3", "p_30", weight=5.0)

    return graph


class CollaborativeGraphRecommenderTestCase(SimpleTestCase):
    def setUp(self):
        self.recommender = CollaborativeGraphRecommender()
        self.recommender.fit(build_test_graph())

    def test_algorithm_name(self):
        self.assertEqual(
            self.recommender.algorithm_name,
            "collaborative",
        )

    def test_jaccard_similarity(self):
        similarity = self.recommender._jaccard(
            {"p_1", "p_2"},
            {"p_2", "p_3"},
        )

        self.assertAlmostEqual(similarity, 1 / 3)

    def test_jaccard_identical_sets(self):
        similarity = self.recommender._jaccard(
            {"p_1", "p_2"},
            {"p_1", "p_2"},
        )

        self.assertEqual(similarity, 1.0)

    def test_jaccard_disjoint_sets(self):
        similarity = self.recommender._jaccard(
            {"p_1"},
            {"p_2"},
        )

        self.assertEqual(similarity, 0.0)

    def test_jaccard_empty_set(self):
        self.assertEqual(
            self.recommender._jaccard(set(), {"p_1"}),
            0.0,
        )

    def test_recommends_related_product(self):
        recs = self.recommender.recommend(
            user_id=1,
            top_k=5,
        )

        recommended_ids = [product_id for product_id, _ in recs]

        self.assertIn(20, recommended_ids)

    def test_does_not_recommend_seen_product(self):
        recs = self.recommender.recommend(
            user_id=1,
            top_k=5,
        )

        recommended_ids = [product_id for product_id, _ in recs]

        self.assertNotIn(10, recommended_ids)

    def test_does_not_recommend_unrelated_product(self):
        recs = self.recommender.recommend(
            user_id=1,
            top_k=5,
        )

        recommended_ids = [product_id for product_id, _ in recs]

        self.assertNotIn(30, recommended_ids)

    def test_unknown_user_returns_empty(self):
        recs = self.recommender.recommend(
            user_id=999,
            top_k=5,
        )

        self.assertEqual(recs, [])

    def test_top_k_is_respected(self):
        recs = self.recommender.recommend(
            user_id=1,
            top_k=1,
        )

        self.assertLessEqual(len(recs), 1)

    def test_recommendations_are_sorted_by_score(self):
        recs = self.recommender.recommend(
            user_id=1,
            top_k=5,
        )

        scores = [score for _, score in recs]

        self.assertEqual(scores, sorted(scores, reverse=True))
