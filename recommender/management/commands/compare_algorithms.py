import networkx as nx
from django.contrib.auth import get_user_model
from django.core.management.base import BaseCommand
from interactions.models import Interaction
from recommender.evaluation import ndcg_at_k, precision_at_k, recall_at_k
from recommender.registry import get_recommender_class

User = get_user_model()


class Command(BaseCommand):
    help = (
        'Строит граф по train-выборке, обучает модель и считает метрики на тесте'
    )

    def add_arguments(self, parser):
        parser.add_argument(
            '--algorithm',
            type=str,
            required=True,
            help='Название алгоритма (pagerank или collaborative)',
        )
        parser.add_argument(
            '--k', type=int, default=10, help='Количество рекомендаций K'
        )
        parser.add_argument(
            '--test-ratio',
            type=float,
            default=0.2,
            help='Доля последних взаимодействий для теста',
        )

    def handle(self, *args, **options):
        algorithm = options['algorithm']
        k = options['k']
        test_ratio = options['test_ratio']

        self.stdout.write(
            f'Подготовка данных и хронологический сплит ({test_ratio*100}% тест)...'
        )

        train_interactions = []
        user_test_products = {}

        for user in User.objects.iterator():
            user_ints = list(
                Interaction.objects.filter(user=user).order_by('timestamp')
            )
            if len(user_ints) < 5:
                train_interactions.extend(user_ints)
                continue

            split_idx = int(len(user_ints) * (1 - test_ratio))
            train_part = user_ints[:split_idx]
            test_part = user_ints[split_idx:]

            train_interactions.extend(train_part)
            user_test_products[user.id] = set(i.product_id for i in test_part)

        if not user_test_products:
            self.stdout.write(
                self.style.ERROR(
                    'Недостаточно данных для формирования тестовой выборки.'
                )
            )
            return

        # Строим граф ТОЛЬКО по train-взаимодействиям
        self.stdout.write('Построение обучающего графа (train graph)...')
        graph = nx.Graph()
        for interaction in train_interactions:
            u_node = f'u_{interaction.user_id}'
            p_node = f'p_{interaction.product_id}'

            graph.add_node(u_node, bipartite=0, type='user')
            graph.add_node(p_node, bipartite=1, type='product')

            if graph.has_edge(u_node, p_node):
                graph[u_node][p_node]['weight'] += interaction.weight
            else:
                graph.add_edge(u_node, p_node, weight=interaction.weight)

        # Инициализируем и обучаем модель на train-графе
        self.stdout.write(f'Обучение модели {algorithm} на train-графе...')
        recommender_cls = get_recommender_class(algorithm)
        recommender = recommender_cls()
        recommender.fit(graph)

        # Оцениваем метрики
        self.stdout.write('Расчет метрик на тестовой выборке...')
        precisions, recalls, ndcgs = [], [], []

        for user_id, test_products in user_test_products.items():
            if not test_products:
                continue

            recs = recommender.recommend(user_id=user_id, top_k=k)
            recommended_ids = [prod_id for prod_id, _ in recs]

            precisions.append(precision_at_k(recommended_ids, test_products, k))
            recalls.append(recall_at_k(recommended_ids, test_products, k))
            ndcgs.append(ndcg_at_k(recommended_ids, test_products, k))

        if not precisions:
            self.stdout.write(
                self.style.WARNING(
                    'Не удалось рассчитать метрики (нет пользователей с тестовыми товарами).'
                )
            )
            return

        avg_precision = sum(precisions) / len(precisions)
        avg_recall = sum(recalls) / len(recalls)
        avg_ndcg = sum(ndcgs) / len(ndcgs)

        self.stdout.write(
            self.style.SUCCESS(
                f'Результаты для модели {algorithm}:\n'
                f'  Precision@{k} = {avg_precision:.4f}\n'
                f'  Recall@{k}    = {avg_recall:.4f}\n'
                f'  NDCG@{k}      = {avg_ndcg:.4f}'
            )
        )