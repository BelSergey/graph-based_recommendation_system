

from collections import defaultdict

from django.core.exceptions import ObjectDoesNotExist
from django.core.management.base import BaseCommand

from interactions.models import Interaction
from recommender.algorithms.pagerank import PageRankRecommender
from recommender.evaluation import ndcg_at_k, precision_at_k, recall_at_k
from recommender.models import RecommendationModel
from recommender.registry import get_recommender_class
from users.models import User
import networkx as nx
from time import perf_counter

MIN_INTERACTIONS_FOR_TEST_SPLIT = 5


class Command(BaseCommand):
    help = (
        "Хронологический train/test split по каждому пользователю, "
        "расчёт Precision@K/Recall@K/NDCG@K и сохранение метрик в активную модель"
    )

    def add_arguments(self, parser):
        parser.add_argument("--algorithm", required=True)
        parser.add_argument("--k", type=int, default=10)
        parser.add_argument("--test-ratio", type=float, default=0.2)

    def handle(self, *args, **options):
        started_at = perf_counter()
        algorithm = options["algorithm"]
        k = options["k"]
        test_ratio = options["test_ratio"]

        # --- 2.1: устранение N+1 — один запрос вместо одного на пользователя ---
        interactions_by_user = defaultdict(list)
        for interaction in Interaction.objects.select_related("user").order_by(
            "user_id", "timestamp"
        ):
            interactions_by_user[interaction.user_id].append(interaction)

        train_interactions = []
        test_interactions = []

        for user in User.objects.iterator():
            user_ints = interactions_by_user.get(user.id, [])

            # Пользователей с малой историей целиком отправляем в train —
            # оценивать рекомендации для них по 1-2 взаимодействиям бессмысленно
            if len(user_ints) < MIN_INTERACTIONS_FOR_TEST_SPLIT:
                train_interactions.extend(user_ints)
                continue

            split_idx = int(len(user_ints) * (1 - test_ratio))
            user_train = user_ints[:split_idx]
            user_test = user_ints[split_idx:]

            train_interactions.extend(user_train)
            test_interactions.extend(user_test)

            # --- 3.3: диагностика пересечений train/test по товару ---
            train_products = {i.product_id for i in user_train}
            test_products = {i.product_id for i in user_test}

            overlap = train_products & test_products
            if overlap:
                self.stdout.write(self.style.WARNING(
                    f"User {user.id}: {len(overlap)} товаров пересекаются между train и test "
                    f"(вероятно, повторные Interaction с одним товаром в разное время)"
                ))

        if not test_interactions:
            self.stdout.write(
                self.style.ERROR(
                    "Нет ни одного пользователя с достаточной историей для test-выборки"
                )
            )
            return
        split_finished_at = perf_counter()

        # --- граф строится ТОЛЬКО из train — иначе модель "увидит" test при обучении ---

        graph = build_interaction_graph_from_interactions(train_interactions)

        graph_finished_at = perf_counter()

        recommender_cls = get_recommender_class(algorithm)
        if algorithm == "pagerank":
            recommender = PageRankRecommender()
        else:
            recommender = recommender_cls()

        recommender.fit(graph)

        fit_finished_at = perf_counter()

        # --- эталон: какие товары пользователь реально взаимодействовал в test ---
        relevant_by_user = defaultdict(set)
        for interaction in test_interactions:
            relevant_by_user[interaction.user_id].add(interaction.product_id)

        precisions, recalls, ndcgs = [], [], []
        users_evaluated = 0

        evaluation_started_at = perf_counter()
        recommendations_by_user = recommender.recommend_many(
            list(relevant_by_user.keys()),
            top_k=k,
        )

        for user_id, relevant in relevant_by_user.items():
            recommended = [
                product_id for product_id, _ in recommendations_by_user.get(user_id, [])
            ]

            if not recommended:
                continue

            precisions.append(precision_at_k(recommended, relevant, k))
            recalls.append(recall_at_k(recommended, relevant, k))
            ndcgs.append(ndcg_at_k(recommended, relevant, k))

            users_evaluated += 1
        evaluation_finished_at = perf_counter()

        if users_evaluated == 0:
            self.stdout.write(
                self.style.ERROR(
                    "Ни для одного пользователя не удалось получить рекомендации"
                )
            )
            return

        avg_precision = sum(precisions) / len(precisions)
        avg_recall = sum(recalls) / len(recalls)
        avg_ndcg = sum(ndcgs) / len(ndcgs)

        self.stdout.write(
            self.style.SUCCESS(
                f"Algorithm: {algorithm}\n"
                f"  Users evaluated: {users_evaluated}\n"
                f"  Train interactions: {len(train_interactions)}\n"
                f"  Test interactions:  {len(test_interactions)}\n"
                f"  Precision@{k} = {avg_precision:.4f}\n"
                f"  Recall@{k}    = {avg_recall:.4f}\n"
                f"  NDCG@{k}      = {avg_ndcg:.4f}"
            )
        )

        # --- 1.1: пишем метрики только в активную модель, а не во все версии ---
        try:
            model = RecommendationModel.objects.get(algorithm=algorithm, is_active=True)
        except ObjectDoesNotExist:
            self.stdout.write(
                self.style.ERROR(
                    f'Нет активной модели для алгоритма "{algorithm}" — '
                    f"сначала запусти train_model --algorithm={algorithm}"
                )
            )
            return

        model.metrics = {
            f"precision@{k}": round(avg_precision, 4),
            f"recall@{k}": round(avg_recall, 4),
            f"ndcg@{k}": round(avg_ndcg, 4),
        }
        model.parameters = {
            "k": k,
            "test_ratio": test_ratio,
            "users_evaluated": users_evaluated,
            "train_interactions": len(train_interactions),
            "test_interactions": len(test_interactions),
        }
        model.save(update_fields=["metrics", "parameters"])
        finished_at = perf_counter()

        self.stdout.write(
            self.style.WARNING(
                "\nВремя выполнения:"
                f"\n  Split:      "
                f"{split_finished_at - started_at:.3f} сек."
                f"\n  Graph:      "
                f"{graph_finished_at - split_finished_at:.3f} сек."
                f"\n  Fit:        "
                f"{fit_finished_at - graph_finished_at:.3f} сек."
                f"\n  Evaluation: "
                f"{evaluation_finished_at - evaluation_started_at:.3f} сек."
                f"\n  Recommend calls: "
                f"{recommender.recommend_calls}"
                f"\n  Total:      "
                f"{finished_at - started_at:.3f} сек."
            )
        )


def build_interaction_graph_from_interactions(interactions) -> "nx.Graph":
    """
    Строит граф из уже загруженного списка Interaction (а не заново из БД,
    как build_interaction_graph()) — нужно, чтобы обучать модель строго
    на train-выборке, не подглядывая в test.
    """
    graph = nx.Graph()
    for interaction in interactions:
        u_node = f"u_{interaction.user_id}"
        p_node = f"p_{interaction.product_id}"

        graph.add_node(u_node, bipartite=0, type="user")
        graph.add_node(p_node, bipartite=1, type="product")

        if graph.has_edge(u_node, p_node):
            graph[u_node][p_node]["weight"] += interaction.weight
        else:
            graph.add_edge(u_node, p_node, weight=interaction.weight)

    return graph
