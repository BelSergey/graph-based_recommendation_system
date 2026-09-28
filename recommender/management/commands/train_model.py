import os

from django.conf import settings
from django.core.management import BaseCommand
from django.db import transaction

from recommender.graph_builder import build_interaction_graph
from recommender.registry import get_recommender_class
from recommender.models import RecommendationModel


class Command(BaseCommand):
    """Обучает и активирует модель рекомендаций."""

    help = "Обучает модель рекомендаций и сохраняет её состояние"

    def add_arguments(self, parser):
        """Добавляет аргументы команды."""
        parser.add_argument("--algorithm", required=True)
        parser.add_argument("--model-version", default="latest")

    def handle(self, *args, **options):
        """Выполняет management-команду."""
        algorithm = options["algorithm"]
        version = options["model_version"]

        graph = build_interaction_graph()
        recommender_cls = get_recommender_class(algorithm)
        recommender = recommender_cls()
        recommender.fit(graph)

        storage_dir = os.path.join(settings.BASE_DIR, "storage", "models")
        os.makedirs(storage_dir, exist_ok=True)
        file_path = os.path.join(storage_dir, f"{algorithm}_v{version}.pkl")
        recommender.save_state(file_path)

        with transaction.atomic():
            RecommendationModel.objects.filter(
                algorithm=algorithm,
                is_active=True,
            ).update(is_active=False)

            RecommendationModel.objects.update_or_create(
                algorithm=algorithm,
                version=version,
                defaults={
                    "file_path": file_path,
                    "is_active": True,
                },
            )

        self.stdout.write(
            self.style.SUCCESS(f"Модель {algorithm} v{version} обучена и активирована")
        )
