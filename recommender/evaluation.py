import math


def precision_at_k(recommended: list[int], relevant: set[int], k: int) -> float:
    """Вычисляет Precision@K."""
    top_k = recommended[:k]
    if not top_k:
        return 0.0
    hits = len(set(top_k) & relevant)
    return hits / len(top_k)


def recall_at_k(recommended: list[int], relevant: set[int], k: int) -> float:
    """Вычисляет Recall@K."""
    if not relevant:
        return 0.0
    top_k = recommended[:k]
    hits = len(set(top_k) & relevant)
    return hits / len(relevant)


def ndcg_at_k(recommended: list[int], relevant: set[int], k: int) -> float:
    """Вычисляет NDCG@K."""
    dcg = 0.0
    for i, item in enumerate(recommended[:k]):
        if item in relevant:
            dcg += 1 / math.log2(i + 2)

    ideal_hits = min(len(relevant), k)
    idcg = sum(1 / math.log2(i + 2) for i in range(ideal_hits))
    return dcg / idcg if idcg > 0 else 0.0
