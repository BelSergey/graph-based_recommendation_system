import networkx as nx
from collections import defaultdict
from .base import BaseRecommender


class CollaborativeGraphRecommender(BaseRecommender):
    algorithm_name = 'collaborative'

    def __init__(self):
        self.graph: nx.Graph | None = None

    def fit(self, graph: nx.Graph) -> None:
        self.graph = graph

    def _jaccard(self, set_a: set, set_b: set) -> float:
        if not set_a or not set_b:
            return 0.0
        intersection = len(set_a & set_b)
        union = len(set_a | set_b)
        return intersection / union if union else 0.0

    def recommend(self, user_id: int, top_k: int = 10) -> list[tuple[int, float]]:
        user_node = f'u_{user_id}'
        if self.graph is None or user_node not in self.graph:
            return []

        target_products = set(self.graph.neighbors(user_node))

        candidate_users = set()
        for product in target_products:
            candidate_users.update(self.graph.neighbors(product))
        candidate_users.discard(user_node)

        scored_products: dict[str, float] = defaultdict(float)
        for other_user in candidate_users:
            other_products = set(self.graph.neighbors(other_user))
            similarity = self._jaccard(target_products, other_products)
            if similarity == 0:
                continue
            for product in other_products - target_products:
                weight = self.graph[other_user][product]['weight']
                scored_products[product] += similarity * weight

        result = [
            (int(node[2:]), score) for node, score in scored_products.items()
        ]
        result.sort(key=lambda x: x[1], reverse=True)
        return result[:top_k]
