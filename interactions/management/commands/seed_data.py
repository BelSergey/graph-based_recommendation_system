import random
from django.core.management.base import BaseCommand
from django.contrib.auth import get_user_model
from apps.catalog.models import Category, Product
from apps.interactions.models import Interaction, InteractionType

User = get_user_model()


class Command(BaseCommand):
    help = 'Генерирует синтетические данные для графа рекомендаций'

    def add_arguments(self, parser):
        parser.add_argument('--users', type=int, default=200)
        parser.add_argument('--products', type=int, default=500)
        parser.add_argument('--interactions', type=int, default=5000)

    def handle(self, *args, **options):
        categories = [
            Category.objects.get_or_create(name=name)[0]
            for name in ['Электроника', 'Одежда', 'Дом', 'Спорт', 'Книги']
        ]

        products = [
            Product.objects.create(
                title=f'Товар {i}',
                category=random.choice(categories),
                price=random.randint(100, 10000),
            )
            for i in range(options['products'])
        ]

        users = [
            User.objects.create_user(username=f'user_{i}', password='test1234')
            for i in range(options['users'])
        ]


        for user in users:
            preferred_category = random.choice(categories)
            preferred_products = [p for p in products if p.category == preferred_category]
            pool = preferred_products * 3 + products

            n = random.randint(5, 40)
            for _ in range(n):
                product = random.choice(pool)
                itype = random.choices(
                    [InteractionType.VIEW, InteractionType.CART, InteractionType.PURCHASE],
                    weights=[0.7, 0.2, 0.1],
                )[0]
                Interaction.objects.create(user=user, product=product, type=itype)

        self.stdout.write(self.style.SUCCESS('Синтетические данные созданы'))
