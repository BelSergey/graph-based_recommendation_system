import networkx as nx
from django.test import SimpleTestCase
from recommender.algorithms.pagerank import PageRankRecommender


def build_test_graph():
    """
    Два пользователя (1, 2) любят один и тот же товар (10).
    У пользователя 2 есть ещё товар (20), которого нет у пользователя 1.
    Ожидание: пользователю 1 система должна предложить товар 20
    (он "близок" через общего пользователя 2), а не товар 30,
    который вообще никак не связан с этим кластером.
    """
    graph = nx.Graph()
    graph.add_edge('u_1', 'p_10', weight=5.0)
    graph.add_edge('u_2', 'p_10', weight=5.0)
    graph.add_edge('u_2', 'p_20', weight=5.0)
    graph.add_edge('u_3', 'p_30', weight=5.0) 
    return graph


class PageRankRecommenderTestCase(SimpleTestCase):
    def setUp(self):
        self.recommender = PageRankRecommender()
        self.recommender.fit(build_test_graph())

    def test_recommends_related_product(self):
        recs = self.recommender.recommend(user_id=1, top_k=5)
        recommended_ids = [product_id for product_id, _ in recs]

        self.assertIn(20, recommended_ids)

    def test_does_not_recommend_already_seen_product(self):
        recs = self.recommender.recommend(user_id=1, top_k=5)
        recommended_ids = [product_id for product_id, _ in recs]

        self.assertNotIn(10, recommended_ids)  # уже видел

    def test_unrelated_product_scores_lower(self):
        recs = self.recommender.recommend(user_id=1, top_k=5)
        scores = dict(recs)

        if 30 in scores and 20 in scores:
            self.assertGreater(scores[20], scores[30])

    def test_unknown_user_returns_empty(self):
        recs = self.recommender.recommend(user_id=999, top_k=5)
        self.assertEqual(recs, [])