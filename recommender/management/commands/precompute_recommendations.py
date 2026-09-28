"""Предвычисление рекомендаций для всех пользователей."""

from django.core.management.base import BaseCommand

from recommender.models import RecommendationModel, RecommendationResult
from recommender.registry import get_recommender_class
from users.models import User


class Command(BaseCommand):
    """Пересчитывает и сохраняет рекомендации для всех пользователей."""

    help = "Пересчитывает и сохраняет рекомендации для всех пользователей"

    def add_arguments(self, parser) -> None:
        """Добавляет аргументы команды."""
        parser.add_argument("--algorithm", required=True)
        parser.add_argument("--model-version", default=None)
        parser.add_argument("--top-k", type=int, default=10)

    def handle(self, *args, **options) -> None:
        """Выполняет предвычисление рекомендаций."""
        algorithm = options["algorithm"]
        version = options["model_version"]

        if version:
            model_record = RecommendationModel.objects.get(
                algorithm=algorithm,
                version=version,
            )
        else:
            model_record = RecommendationModel.objects.get(
                algorithm=algorithm,
                is_active=True,
            )

        recommender_cls = get_recommender_class(algorithm)
        recommender = recommender_cls()
        recommender.load_state(model_record.file_path)

        user_ids = list(User.objects.values_list("id", flat=True))

        recommendations_by_user = recommender.recommend_many(
            user_ids,
            top_k=options["top_k"],
        )

        RecommendationResult.objects.filter(model=model_record).delete()

        results = [
            RecommendationResult(
                user_id=user_id,
                model=model_record,
                product_id=product_id,
                score=score,
            )
            for user_id, recs in recommendations_by_user.items()
            for product_id, score in recs
        ]

        RecommendationResult.objects.bulk_create(
            results,
            batch_size=1000,
        )

        self.stdout.write(
            self.style.SUCCESS(
                f"Сохранено {len(results)} рекомендаций "
                f"для {algorithm} v{model_record.version}"
            )
        )
