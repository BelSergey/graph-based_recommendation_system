# recommender/algorithms/pagerank.py

import heapq

import networkx as nx

from .base import BaseRecommender


class PageRankRecommender(BaseRecommender):
    algorithm_name = "pagerank"

    def __init__(self, alpha: float = 0.85, max_iter: int = 30, tol: float = 1e-4):
        self.alpha = alpha
        self.max_iter = max_iter
        self.tol = tol
        self.graph = None
        self.recommend_calls = 0

    def fit(self, graph: nx.Graph) -> None:
        self.graph = graph

    def recommend(self, user_id: int, top_k: int = 10) -> list[tuple[int, float]]:
        self.recommend_calls += 1

        user_node = f"u_{user_id}"
        if self.graph is None or user_node not in self.graph:
            return []

        personalization = {user_node: 1.0}
        scores = nx.pagerank(
            self.graph,
            alpha=self.alpha,
            personalization=personalization,
            weight="weight",
            max_iter=self.max_iter,
            tol=self.tol,
        )

        already_seen = set(self.graph.neighbors(user_node))
        product_scores = (
            (int(node[2:]), score)
            for node, score in scores.items()
            if node.startswith("p_") and node not in already_seen
        )

        return heapq.nlargest(top_k, product_scores, key=lambda item: item[1])