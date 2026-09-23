from django.core.management.base import BaseCommand
from django.contrib.auth import get_user_model
from recommender.registry import get_recommender_class
from recommender.models import RecommendationModel, RecommendationResult

User = get_user_model()


class Command(BaseCommand):
    help = 'Пересчитывает и сохраняет рекомендации для всех пользователей'

    def add_arguments(self, parser):
        parser.add_argument('--algorithm', required=True)
        parser.add_argument('--model-version', default='1')
        parser.add_argument('--top-k', type=int, default=10)

    def handle(self, *args, **options):
        model_record = RecommendationModel.objects.get(
            algorithm=options['algorithm'], version=options['model_version']
        )

        recommender_cls = get_recommender_class(options['algorithm'])
        recommender = recommender_cls()
        recommender.load_state(model_record.file_path)

        RecommendationResult.objects.filter(model=model_record).delete()

        results = []
        for user in User.objects.all():
            recs = recommender.recommend(user.id, top_k=options['top_k'])
            for product_id, score in recs:
                results.append(RecommendationResult(
                    user=user, model=model_record,
                    product_id=product_id, score=score,
                ))

        RecommendationResult.objects.bulk_create(results, batch_size=1000)
        self.stdout.write(self.style.SUCCESS(f'Сохранено {len(results)} рекомендаций'))