from .algorithms.base import BaseRecommender
from .algorithms.collaborative import CollaborativeGraphRecommender
from .algorithms.pagerank import PageRankRecommender

ALGORITHM_REGISTRY: dict[str, type[BaseRecommender]] = {
    "pagerank": PageRankRecommender,
    "collaborative": CollaborativeGraphRecommender,
}


def get_recommender_class(name: str) -> type[BaseRecommender]:
    """Возвращает класс рекомендателя по имени алгоритма."""
    if name not in ALGORITHM_REGISTRY:
        raise ValueError(f"Unknown algorithm: {name}")

    return ALGORITHM_REGISTRY[name]
