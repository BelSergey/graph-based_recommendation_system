# GBRS — Graph-Based Recommendation System

Рекомендательная система товаров на основе графов для маркетплейса.
Дипломный проект (курс "Python-разработчик"): Django + Django REST Framework +
PostgreSQL + NetworkX, с возможностью переключения между алгоритмами
рекомендаций и сохранением промежуточных результатов.

## Содержание

- [Архитектура](#архитектура)
- [Стек технологий](#стек-технологий)
- [Модель данных](#модель-данных)
- [Алгоритмы рекомендаций](#алгоритмы-рекомендаций)
- [Production и оценка](#production-и-оценка)
- [Результаты эксперимента](#результаты-эксперимента)
- [Быстрый старт (Docker)](#быстрый-старт-docker)
- [Локальная разработка (без Docker)](#локальная-разработка-без-docker)
- [Переменные окружения](#переменные-окружения)
- [Management-команды](#management-команды)
- [API](#api)
- [Тестирование](#тестирование)
- [Проверка проекта](#проверка-проекта)
- [CI](#ci)
- [Структура проекта](#структура-проекта)

## Архитектура

Система строит взвешенный bipartite-граф "пользователь — товар" на основе
истории взаимодействий (просмотры, добавления в корзину, покупки) и
применяет к нему один из графовых алгоритмов для генерации персональных
рекомендаций.

```
┌─────────────┐     ┌──────────────────┐     ┌──────────────────┐
│ Interaction │ --> │  graph_builder   │ --> │  networkx.Graph  │
│  (Django)   │     │                  │     │  (в памяти)      │
└─────────────┘     └──────────────────┘     └────────┬─────────┘
                                                        │
                                                        v
                                          ┌─────────────────────────┐
                                          │   BaseRecommender       │
                                          │  (Strategy Pattern)     │
                                          │  ┌─────────────────────┐│
                                          │  │ PageRankRecommender ││ 
                                          │  ├─────────────────────┤│
                                          │  │ CollaborativeGraph… ││
                                          │  └─────────────────────┘│
                                          └────────────┬────────────┘
                                                        │
                                                        v
                                       ┌─────────────────────────────┐
                                       │  RecommendationResult (БД)  │
                                       │  — предвычисленный кэш      │
                                       └──────────────┬──────────────┘
                                                       │
                                                       v
                                            GET /api/recommendations/
```

Алгоритмы реализуют общий интерфейс `BaseRecommender` (`fit`/`recommend`/
`save_state`/`load_state`), поэтому переключение между ними — это смена
одной строки в реестре `ALGORITHM_REGISTRY`, без изменений в API или
management-командах.

## Стек технологий

- **Backend:** Django 5, Django REST Framework
- **База данных:** PostgreSQL
- **Граф и алгоритмы:** NetworkX (PageRank, коллаборативная фильтрация)
- **Документация API:** drf-spectacular (OpenAPI/Swagger)
- **Деплой:** Docker, docker-compose, nginx, gunicorn
- **Архитектура контейнеров:** PostgreSQL + Django/Gunicorn + Nginx

## Модель данных

Основные сущности системы:

| Модель | Назначение |
|---|---|
| `users.User` | Пользователь системы (кастомная модель на базе `AbstractUser`) |
| `catalog.Product` | Товар каталога: название, описание, категория, цена |
| `interactions.Interaction` | Связь пользователя с товаром и история взаимодействий |
| `recommender.RecommendationModel` | Метаданные обученной модели и её сохранённое состояние |
| `recommender.RecommendationResult` | Предвычисленная рекомендация товара пользователю |

### Веса взаимодействий

Каждому типу взаимодействия соответствует числовой вес:

| Тип | Вес |
|---|---:|
| `VIEW` | 1.0 |
| `CART` | 3.0 |
| `PURCHASE` | 5.0 |

Вес пересчитывается автоматически при сохранении `Interaction`.
При построении графа повторные взаимодействия одной пары
`user + product` агрегируются по сумме весов.

Например:

```text
VIEW + CART + PURCHASE = 1 + 3 + 5 = 9
```

Так граф хранит не только факт взаимодействия, но и его силу.

## Алгоритмы рекомендаций

| Алгоритм | Идея | Плюсы | Минусы |
|---|---|---|---|
| **PageRank** (Personalized PageRank) | Случайное блуждание по графу с "телепортацией" в узел пользователя | Учитывает многошаговые связи, устойчив к шуму | Дороже в вычислении на больших графах |
| **Collaborative Filtering** (граф, коэффициент Жаккара) | Поиск похожих пользователей через общих соседей 2-го порядка | Просто и быстро, легко объяснить | Хуже работает при малом числе пересечений (холодный старт) |

### Параметры реализации

Для Personalized PageRank используются параметры по умолчанию:
`alpha=0.85`, `max_iter=30`, `tol=1e-4`. Персонализация задаётся на узле
целевого пользователя, а вес рёбер графа учитывается при расчёте PageRank.
Уже просмотренные пользователем товары исключаются из итоговой выдачи.

Collaborative Graph использует коэффициент Жаккара между множествами
товаров двух пользователей. Итоговый score кандидата увеличивается как
`similarity * weight`, после чего рекомендации сортируются по score.
Товары, уже присутствующие в истории целевого пользователя, не добавляются
в результат.

Метрики качества (Precision@K, Recall@K, NDCG@K) считаются на
хронологическом train/test split. По умолчанию последние 20% взаимодействий
каждого пользователя выделяются в test, а оставшиеся 80% используются для
построения обучающего графа. Пользователи с историей менее 5 взаимодействий
целиком остаются в train, поскольку для них отдельная test-выборка слишком
мала. Реализация находится в `compare_algorithms`.

В `BaseRecommender` предусмотрен `recommend_many()`. Для небольших наборов
пользователей используется последовательный расчёт, а для 20 и более
пользователей — `ProcessPoolExecutor`, чтобы параллельно считать рекомендации
на нескольких CPU-ядрах.

## Production и оценка

В проекте разделены два сценария работы.

**Production pipeline:**

```text
train_model
    -> граф из БД
    -> fit алгоритма
    -> состояние модели (.pkl)
    -> RecommendationModel
    -> precompute_recommendations
    -> RecommendationResult
    -> GET /api/recommendations/
```

API не запускает алгоритм рекомендации заново на каждый HTTP-запрос.
Он читает предвычисленные `RecommendationResult` из PostgreSQL.

**Evaluation pipeline:**

```text
Interaction
    -> chronological train/test split
    -> train-граф только из train
    -> fit алгоритма
    -> рекомендации для test-пользователей
    -> Precision@K / Recall@K / NDCG@K
```

Для оценки production-результаты не переиспользуются: алгоритм строится
на train-графе, а test используется только для проверки качества. Это
исключает утечку будущих взаимодействий в граф, по которому строятся
рекомендации.


## Результаты эксперимента

Эксперимент выполнен на датасете **MovieLens 100K** после импорта в модели
Django. В импортированной выборке: **943 пользователя, 1682 фильма и
100 000 взаимодействий**. Для оценки использовался хронологический split с
`test_ratio=0.2` и `K=10`. Фактические размеры выборок после применения
правила для пользователей с малой историей: **79 619 train** и **20 381
test** взаимодействие.

### Качество

| Алгоритм | Precision@10 | Recall@10 | NDCG@10 |
|---|---:|---:|---:|
| PageRank | 0.1238 | 0.0825 | 0.1437 |
| Collaborative Graph | 0.1416 | 0.0964 | 0.1646 |

В этом эксперименте Collaborative Graph дал на **0.0178** больше Precision,
на **0.0139** больше Recall и на **0.0209** больше NDCG по сравнению с
PageRank. Это разница именно для данной выборки, параметров и способа
оценки; она не является гарантией для других датасетов.

### Время

Сравнительный эксперимент выполнялся так: один раз строился train/test split,
далее строился граф только из train, после чего рекомендации для тестовых
пользователей рассчитывались параллельно через `ProcessPoolExecutor`.

| Алгоритм | Время эксперимента |
|---|---:|
| PageRank | 35.54 сек. |
| Collaborative Graph | 22.65 сек. |

Отдельно измерено полное предвычисление top-10 рекомендаций для всех 943
пользователей, включая запись **9 430 результатов** каждого алгоритма в БД:

| Алгоритм | Время precompute | Сохранено |
|---|---:|---:|
| PageRank | 51.20 сек. | 9 430 |
| Collaborative Graph | 24.40 сек. | 9 430 |

В API выдача берётся из `RecommendationResult`, поэтому эти вычисления
выполняются заранее, а не на каждый HTTP-запрос.

## Быстрый старт (Docker)

Нужны только Docker и Docker Compose — Python и PostgreSQL ставить локально
не требуется.

```bash
git clone <ссылка-на-репозиторий>
cd GBRS

cp .env.example .env
# отредактируй .env — как минимум смени SECRET_KEY и DB_PASSWORD

docker compose up --build -d
```

После старта:

```bash
# первый суперюзер для /admin/
docker compose exec web python manage.py createsuperuser

# наполнить БД синтетическими данными
docker compose exec web python manage.py seed_data --users 200 --products 500

# обучить актуальные версии моделей
docker compose exec web python manage.py train_model --algorithm=pagerank --model-version=latest
docker compose exec web python manage.py train_model --algorithm=collaborative --model-version=latest

# предвычислить top-10 для всех пользователей
docker compose exec web python manage.py precompute_recommendations --algorithm=pagerank --model-version=latest --top-k=10
docker compose exec web python manage.py precompute_recommendations --algorithm=collaborative --model-version=latest --top-k=10
```

Приложение доступно на `http://localhost/` (через nginx), админка — на
`http://localhost/admin/`, документация API — на `http://localhost/api/docs/`.

Для MovieLens 100K датасет ожидается в локальной папке `ml-100k/`. В
`docker-compose.yml` она монтируется в контейнер `web` как `/app/ml-100k`
в режиме read-only, поэтому датасет не попадает в Docker-образ.

После помещения датасета в `ml-100k/` его можно импортировать так:

```bash
docker compose exec web python manage.py import_movielens --path ml-100k
```

Логи:

```bash
docker compose logs -f web
```

Остановить:

```bash
docker compose down          # с сохранением данных (volumes)
docker compose down -v       # + удалить volumes (полный сброс БД)
```

## Локальная разработка (без Docker)

Если удобнее работать без контейнеров (например, для отладки в PyCharm):

```bash
python -m venv venv
source venv/bin/activate      # Windows: venv\Scripts\activate

pip install -r requirements.txt

cp .env.example .env
# укажи в .env DB_HOST=localhost и данные локально запущенного PostgreSQL

python manage.py migrate
python manage.py createsuperuser
python manage.py runserver
```

## Переменные окружения

Все настройки читаются из `.env` (см. `.env.example`):

| Переменная | Описание |
|---|---|
| `SECRET_KEY` | Секретный ключ Django |
| `DEBUG` | `True`/`False` |
| `ALLOWED_HOSTS` | Через запятую, например `localhost,127.0.0.1` |
| `DB_NAME`, `DB_USER`, `DB_PASSWORD` | Параметры подключения к PostgreSQL |
| `DB_HOST` | `localhost` для локальной разработки, `db` внутри docker-compose (переопределяется автоматически, см. `docker-compose.yml`) |
| `DB_PORT` | Обычно `5432` |

## Management-команды

| Команда | Назначение |
|---|---|
| `seed_data --users N --products M` | Генерирует синтетический граф взаимодействий |
| `import_movielens --path ml-100k` | Импортирует реальный датасет MovieLens 100k вместо синтетики |
| `train_model --algorithm=<name> --model-version=<v>` | Обучает модель, сохраняет состояние в `storage/models/`, помечает как активную |
| `precompute_recommendations --algorithm=<name> --model-version=<v> --top-k=N` | Пересчитывает и кэширует рекомендации для всех пользователей в БД |
| `compare_algorithms --algorithm=<name> --k=N` | Хронологический train/test split, расчёт Precision@K/Recall@K/NDCG@K |
| `run_experiment --k=N` | Обучает реализованные алгоритмы PageRank и Collaborative Graph и сравнивает их метрики |

Пример полного цикла:

```bash
python manage.py seed_data --users 300 --products 600
python manage.py run_experiment --k 10

# Для реального датасета MovieLens 100K:
python manage.py import_movielens --path ml-100k
python manage.py run_experiment --k 10
python manage.py precompute_recommendations --algorithm=pagerank --model-version=latest --top-k=10
python manage.py precompute_recommendations --algorithm=collaborative --model-version=latest --top-k=10
```

## API

Документация в формате Swagger доступна на `/api/docs/`
(`/api/schema/` — сырая OpenAPI-схема).

### `GET /api/recommendations/`

| Параметр | Обязательный | Описание |
|---|---|---|
| `user_id` | да | ID пользователя |
| `algorithm` | нет | `pagerank` / `collaborative`. Без параметра берётся активная модель |
| `top_k` | нет | Количество рекомендаций (по умолчанию 10, максимум 100) |

```bash
curl "http://localhost/api/recommendations/?user_id=1&algorithm=pagerank&top_k=5"
```

```json
{
  "algorithm": "pagerank",
  "version": "latest",
  "results": [
    {"product": {"id": 42, "title": "Товар 42", "price": "1999.00"}, "score": 0.031},
    ...
  ]
}
```

### `GET /api/algorithms/`

Список всех обученных моделей с их метриками и статусом активности.

```bash
curl "http://localhost/api/algorithms/"
```

Готовая Postman-коллекция для ручного тестирования — в папке `postman/`.

## Тестирование

```bash
# локально
python manage.py test

# в докере
docker compose exec web python manage.py test
```

Покрытие:
- `recommender/tests/test_graph_builder.py` — построение графа из БД
- `recommender/tests/test_pagerank.py`, `test_collaborative.py` — алгоритмы на синтетических графах
- `recommender/tests/test_api.py` — интеграционные тесты API
- `recommender/tests/test_evaluation.py` — Precision@K, Recall@K, NDCG@K
- `recommender/tests/test_models.py`, `test_serializers.py`, `test_registry.py` — модели, сериализаторы и реестр алгоритмов

## Проверка проекта

Перед финальной версией проекта выполнены проверки:

```text
flake8 .
# без ошибок

black --check .
# форматирование соответствует Black

python manage.py test
# 68 тестов, OK

python manage.py check
# без ошибок

python manage.py makemigrations --check --dry-run
# No changes detected

mypy .
# без ошибок
```

## CI

В репозитории настроен GitHub Actions workflow `.github/workflows/ci.yml`.

При push в `main` и `feature/optimisation`, а также при pull request в `main`,
CI выполняет две стадии:

1. `lint` — установка зависимостей, `flake8 .` и `black --check .`.
2. `test` — запуск PostgreSQL 16 как service и `python manage.py test`.

Так базовые проверки стиля и тесты запускаются автоматически до интеграции
изменений в `main`.

## Структура проекта

```
GBRS/
├── config/                 # настройки Django, urls, wsgi/asgi
├── users/                  # кастомная модель User
├── catalog/                # Category, Product
├── interactions/           # Interaction (рёбра графа) + seed_data
├── recommender/
│   ├── algorithms/          # BaseRecommender, PageRank, Collaborative
│   ├── management/commands/ # train_model, precompute_recommendations,
│   │                         # compare_algorithms, run_experiment, import_movielens
│   ├── tests/
│   ├── graph_builder.py
│   ├── evaluation.py        # Precision@K, Recall@K, NDCG@K
│   ├── registry.py          # ALGORITHM_REGISTRY
│   ├── models.py            # RecommendationModel, RecommendationResult
│   ├── serializers.py
│   ├── views.py
│   └── urls.py
├── storage/models/          # сохранённые состояния моделей (.pkl)
├── docker/nginx/nginx.conf
├── Dockerfile
├── docker-compose.yml
├── entrypoint.sh
└── requirements.txt
```

## Roadmap

- [x] PageRank и коллаборативная фильтрация на графе
- [x] REST API с переключением алгоритмов
- [x] Метрики качества и сравнение алгоритмов
- [x] Импорт реального датасета (MovieLens 100k)
- [ ] Node2Vec (графовые эмбеддинги)
- [ ] GNN на PyTorch (GraphSAGE/GCN) для link prediction
