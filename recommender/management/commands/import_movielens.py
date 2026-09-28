import os
import csv
from datetime import datetime, timezone as dt_timezone
from django.core.management.base import BaseCommand
from django.contrib.auth import get_user_model
from catalog.models import Category, Product
from interactions.models import Interaction, InteractionType

User = get_user_model()


class Command(BaseCommand):
    """Импортирует данные MovieLens в PostgreSQL."""

    help = "Импортирует датасет MovieLens 100k с сохранением исторических дат и типов"

    def add_arguments(self, parser):
        """Добавляет аргументы команды."""
        parser.add_argument(
            "--path",
            type=str,
            default="ml-100k",
            help="Путь к папке с распакованным датасетом ml-100k",
        )

    def handle(self, *args, **options):
        """Выполняет management-команду."""
        dataset_path = options["path"]
        users_file = os.path.join(dataset_path, "u.user")
        items_file = os.path.join(dataset_path, "u.item")
        data_file = os.path.join(dataset_path, "u.data")

        if not os.path.exists(dataset_path):
            self.stdout.write(self.style.ERROR(f"Папка не найдена: {dataset_path}"))
            return

        self.stdout.write("Очистка старых данных...")
        Interaction.objects.all().delete()
        Product.objects.all().delete()
        Category.objects.all().delete()

        movie_category, _ = Category.objects.get_or_create(name="Кинематограф")

        self.stdout.write("Импорт пользователей...")
        user_id_map = {}
        with open(users_file, "r", encoding="latin-1") as f:
            for line in f:
                parts = line.strip().split("|")
                old_id = parts[0]
                username = f"ml_user_{old_id}"
                user, _ = User.objects.get_or_create(
                    username=username, defaults={"email": f"{username}@movielens.test"}
                )
                user_id_map[old_id] = user.id

        self.stdout.write("Импорт фильмов...")
        product_id_map = {}
        with open(items_file, "r", encoding="latin-1") as f:
            for line in f:
                parts = line.split("|")
                old_id = parts[0]
                title = parts[1]
                product = Product.objects.create(
                    title=title, category=movie_category, price=0.00
                )
                product_id_map[old_id] = product.id

        self.stdout.write("Импорт взаимодействий (с историческими таймстемпами)...")
        interactions_to_create = []

        with open(data_file, "r", encoding="latin-1") as f:
            reader = csv.reader(f, delimiter="\t")
            for row in reader:
                if len(row) < 4:
                    continue
                old_u_id, old_i_id, rating, timestamp = row[0], row[1], row[2], row[3]

                if old_u_id not in user_id_map or old_i_id not in product_id_map:
                    continue

                dt_aware = datetime.fromtimestamp(int(timestamp), tz=dt_timezone.utc)

                interactions_to_create.append(
                    Interaction(
                        user_id=user_id_map[old_u_id],
                        product_id=product_id_map[old_i_id],
                        type=InteractionType.VIEW,
                        weight=float(rating),
                        timestamp=dt_aware,
                    )
                )

        Interaction.objects.bulk_create(interactions_to_create, batch_size=1000)

        self.stdout.write(
            self.style.SUCCESS(
                f"Импорт завершен! Пользователей: {len(user_id_map)}, "
                f"фильмов: {len(product_id_map)}, взаимодействий: {len(interactions_to_create)}"
            )
        )
