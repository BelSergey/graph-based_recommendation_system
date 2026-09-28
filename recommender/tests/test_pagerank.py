import networkx as nx
from django.test import SimpleTestCase

from recommender.algorithms.pagerank import PageRankRecommender


def build_test_graph():
    graph = nx.Graph()

    graph.add_edge("u_1", "p_10", weight=5.0)

    graph.add_edge("u_2", "p_10", weight=5.0)
    graph.add_edge("u_2", "p_20", weight=5.0)

    graph.add_edge("u_3", "p_30", weight=5.0)

    return graph


class PageRankRecommenderTestCase(SimpleTestCase):
    def setUp(self):
        self.recommender = PageRankRecommender(
            max_iter=100,
            tol=1e-6,
        )
        self.recommender.fit(build_test_graph())

    def test_algorithm_name(self):
        self.assertEqual(
            self.recommender.algorithm_name,
            "pagerank",
        )

    def test_default_alpha(self):
        self.assertEqual(
            self.recommender.alpha,
            0.85,
        )

    def test_recommends_related_product(self):
        recs = self.recommender.recommend(
            user_id=1,
            top_k=5,
        )

        recommended_ids = [product_id for product_id, _ in recs]

        self.assertIn(20, recommended_ids)

    def test_does_not_recommend_already_seen_product(self):
        recs = self.recommender.recommend(
            user_id=1,
            top_k=5,
        )

        recommended_ids = [product_id for product_id, _ in recs]

        self.assertNotIn(10, recommended_ids)

    def test_unrelated_product_scores_lower(self):
        recs = self.recommender.recommend(
            user_id=1,
            top_k=5,
        )

        scores = dict(recs)

        if 30 in scores and 20 in scores:
            self.assertGreater(scores[20], scores[30])

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

    def test_fit_stores_graph(self):
        self.assertIsNotNone(self.recommender.graph)
        self.assertIn("u_1", self.recommender.graph)
        self.assertIn("p_10", self.recommender.graph)
