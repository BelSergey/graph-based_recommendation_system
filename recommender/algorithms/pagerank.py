import networkx as nx
from .base import BaseRecommender


class PageRankRecommender(BaseRecommender):
    algorithm_name = "pagerank"

    def __init__(self, alpha: float = 0.85):
        self.alpha = alpha
        self.graph: nx.Graph | None = None

    def fit(self, graph: nx.Graph) -> None:
        self.graph = graph

    def recommend(self, user_id: int, top_k: int = 10) -> list[tuple[int, float]]:
        user_node = f"u_{user_id}"
        if self.graph is None or user_node not in self.graph:
            return []

        personalization = {node: 0 for node in self.graph.nodes}
        personalization[user_node] = 1

        scores = nx.pagerank(
            self.graph,
            alpha=self.alpha,
            personalization=personalization,
            weight="weight",
        )

        already_seen = set(self.graph.neighbors(user_node))
        product_scores = [
            (int(node[2:]), score)
            for node, score in scores.items()
            if node.startswith("p_") and node not in already_seen
        ]

        product_scores.sort(key=lambda x: x[1], reverse=True)
        return product_scores[:top_k]
