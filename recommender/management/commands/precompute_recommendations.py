from django.core.management.base import BaseCommand
from recommender.registry import get_recommender_class
from recommender.models import RecommendationModel, RecommendationResult
from users.models import User


class Command(BaseCommand):
    help = "Пересчитывает и сохраняет рекомендации для всех пользователей"

    def add_arguments(self, parser):
        parser.add_argument("--algorithm", required=True)
        parser.add_argument("--model-version", default="latest")
        parser.add_argument("--top-k", type=int, default=10)

    def handle(self, *args, **options):
        model_record = RecommendationModel.objects.get(
            algorithm=options["algorithm"], version=options["model_version"]
        )

        recommender_cls = get_recommender_class(options["algorithm"])
        recommender = recommender_cls()
        recommender.load_state(model_record.file_path)

        # только ID, не полные объекты User — меньше памяти и один компактный SQL-запрос
        user_ids = list(User.objects.values_list("id", flat=True))

        recommendations_by_user = recommender.recommend_many(
            user_ids, top_k=options["top_k"]
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

        RecommendationResult.objects.bulk_create(results, batch_size=1000)
        self.stdout.write(self.style.SUCCESS(f"Сохранено {len(results)} рекомендаций"))