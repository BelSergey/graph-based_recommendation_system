import os
import pickle
from abc import ABC, abstractmethod
from concurrent.futures import ProcessPoolExecutor

import networkx as nx

_worker_recommender: "BaseRecommender | None" = None


def _init_worker(recommender: "BaseRecommender") -> None:
    """
    Инициализирует рекомендатор в процессе-воркере.
    """
    global _worker_recommender
    _worker_recommender = recommender


def _call_recommend(
    user_id: int,
    top_k: int,
) -> tuple[int, list[tuple[int, float]]]:
    assert _worker_recommender is not None
    return user_id, _worker_recommender.recommend(user_id, top_k=top_k)


class BaseRecommender(ABC):
    """
    Общий интерфейс для всех алгоритмов рекомендаций.
    """

    algorithm_name: str = "base"

    @abstractmethod
    def fit(self, graph: nx.Graph) -> None:
        """Обучает рекомендатор на графе взаимодействий."""
        raise NotImplementedError

    @abstractmethod
    def recommend(
        self,
        user_id: int,
        top_k: int = 10,
    ) -> list[tuple[int, float]]:
        """Возвращает top-k рекомендаций для пользователя."""
        raise NotImplementedError

    def save_state(self, path: str) -> None:
        """Сохраняет состояние рекомендатора в файл."""
        with open(path, "wb") as f:
            pickle.dump(self.__dict__, f)

    def load_state(self, path: str) -> None:
        """Загружает состояние рекомендатора из файла."""
        with open(path, "rb") as f:
            self.__dict__.update(pickle.load(f))

    def recommend_many(
        self,
        user_ids: list[int],
        top_k: int = 10,
    ) -> dict[int, list[tuple[int, float]]]:
        """Генерирует рекомендации для нескольких пользователей."""
        if not user_ids:
            return {}

        if len(user_ids) < 20:
            return {uid: self.recommend(uid, top_k=top_k) for uid in user_ids}

        results = {}
        max_workers = min(os.cpu_count() or 4, len(user_ids))
        processed = 0

        with ProcessPoolExecutor(
            max_workers=max_workers,
            initializer=_init_worker,
            initargs=(self,),
        ) as executor:
            for user_id, recs in executor.map(
                _call_recommend,
                user_ids,
                [top_k] * len(user_ids),
                chunksize=1,
            ):
                results[user_id] = recs
                processed += 1

                if processed % 100 == 0:
                    print(f"  обработано " f"{processed}/{len(user_ids)} пользователей")

        return results
