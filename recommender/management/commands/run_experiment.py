from django.core.management.base import BaseCommand
from django.core.management import call_command


class Command(BaseCommand):
    """Обучает и сравнивает зарегистрированные алгоритмы."""

    help = "Запускает полный цикл: обучение всех моделей и их сравнительный анализ"

    def add_arguments(self, parser):
        """Добавляет аргументы команды."""
        parser.add_argument(
            "--k", type=int, default=10, help="Количество рекомендаций K для оценки"
        )

    def handle(self, *args, **options):
        """Выполняет management-команду."""
        k = options["k"]
        algorithms = ["pagerank", "collaborative"]

        self.stdout.write(
            self.style.SUCCESS("=== ЗАПУСК ПАЙПЛАЙНА РЕКОМЕНДАТЕЛЬНОЙ СИСТЕМЫ ===\n")
        )

        for algo in algorithms:
            self.stdout.write(self.style.WARNING(f"--- Обучение модели: {algo} ---"))

            call_command("train_model", algorithm=algo, model_version="latest")
            print()

        self.stdout.write(self.style.SUCCESS("=== СРАВНИТЕЛЬНЫЙ АНАЛИЗ АЛГОРИТМОВ ==="))
        for algo in algorithms:
            self.stdout.write(
                self.style.WARNING(f"--- Оценка метрик для: {algo} (K={k}) ---")
            )
            call_command("compare_algorithms", algorithm=algo, k=k)
            print()

        self.stdout.write(self.style.SUCCESS("=== ЭКСПЕРИМЕНТ УСПЕШНО ЗАВЕРШЕН ==="))
