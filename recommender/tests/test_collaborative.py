import networkx as nx
from django.test import SimpleTestCase
from recommender.algorithms.collaborative import CollaborativeGraphRecommender


def build_test_graph():
    """
    Пользователь 1 и пользователь 2 полностью совпадают по товарам (10, 11)
    — высокий Jaccard. У пользователя 2 есть ещё товар 12.
    Пользователь 3 не пересекается с пользователем 1 вообще.
    """
    graph = nx.Graph()
    graph.add_edge("u_1", "p_10", weight=3.0)
    graph.add_edge("u_1", "p_11", weight=3.0)
    graph.add_edge("u_2", "p_10", weight=3.0)
    graph.add_edge("u_2", "p_11", weight=3.0)
    graph.add_edge("u_2", "p_12", weight=3.0)
    graph.add_edge("u_3", "p_99", weight=3.0)
    return graph


class CollaborativeRecommenderTestCase(SimpleTestCase):
    def setUp(self):
        self.recommender = CollaborativeGraphRecommender()
        self.recommender.fit(build_test_graph())

    def test_recommends_product_from_similar_user(self):
        recs = self.recommender.recommend(user_id=1, top_k=5)
        recommended_ids = [product_id for product_id, _ in recs]

        self.assertIn(12, recommended_ids)

    def test_jaccard_zero_for_disjoint_sets(self):
        similarity = self.recommender._jaccard({"p_10", "p_11"}, {"p_99"})
        self.assertEqual(similarity, 0.0)

    def test_jaccard_one_for_identical_sets(self):
        similarity = self.recommender._jaccard({"p_10", "p_11"}, {"p_10", "p_11"})
        self.assertEqual(similarity, 1.0)

    def test_unrelated_user_not_recommended_from(self):
        recs = self.recommender.recommend(user_id=1, top_k=5)
        recommended_ids = [product_id for product_id, _ in recs]

        self.assertNotIn(99, recommended_ids)
