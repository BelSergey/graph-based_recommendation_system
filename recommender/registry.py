from .algorithms.pagerank import PageRankRecommender
from .algorithms.collaborative import CollaborativeGraphRecommender

ALGORITHM_REGISTRY = {
    'pagerank': PageRankRecommender,
    'collaborative': CollaborativeGraphRecommender,
}


def get_recommender_class(name: str):
    if name not in ALGORITHM_REGISTRY:
        raise ValueError(f'Unknown algorithm: {name}')
    return ALGORITHM_REGISTRY[name]
