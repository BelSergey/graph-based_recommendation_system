from abc import ABC, abstractmethod
import pickle
import networkx as nx


class BaseRecommender(ABC):
    """
    Общий интерфейс для всех алгоритмов рекомендаций.
    Каждый конкретный алгоритм наследуется от этого класса.
    """

    algorithm_name: str = "base"

    @abstractmethod
    def fit(self, graph: nx.Graph) -> None:
        """Обучить/построить модель на графе взаимодействий."""
        raise NotImplementedError

    @abstractmethod
    def recommend(self, user_id: int, top_k: int = 10) -> list[tuple[int, float]]:
        """Вернуть список (product_id, score), отсортированный по убыванию score."""
        raise NotImplementedError

    def save_state(self, path: str) -> None:
        with open(path, "wb") as f:
            pickle.dump(self.__dict__, f)

    def load_state(self, path: str) -> None:
        with open(path, "rb") as f:
            self.__dict__.update(pickle.load(f))
