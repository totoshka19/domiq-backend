# Domiq Backend

REST API для маркетплейса недвижимости. Модульный монолит на FastAPI.

**Swagger (продакшн):** https://domiq-backend.onrender.com/docs

## Стек

- **Python 3.12** + **FastAPI**
- **PostgreSQL** + **SQLAlchemy 2.0** (async) + **Alembic**
- **Redis** + **Celery** — фоновые задачи и email-уведомления
- **S3-совместимое хранилище** (Supabase Storage) — фото объявлений и аватары
- **WebSocket** — чат в реальном времени
- **JWT** (access + refresh токены) с blacklist через Redis

## Продакшн-инфраструктура

| Слой | Сервис |
|---|---|
| API | Render (FastAPI) |
| База данных | Neon (serverless PostgreSQL) |
| Фоновые задачи | Celery worker (не задеплоен — требует платный план) |
| Redis | Upstash (serverless) |
| Файлы | Supabase Storage (S3-совместимый API) |
| Фронтенд | Vercel |

## Быстрый старт

```bash
# Клонировать репозиторий
git clone https://github.com/totoshka19/domiq-backend.git
cd domiq-backend

# Создать виртуальное окружение
python -m venv .venv
.venv\Scripts\activate        # Windows
source .venv/bin/activate     # Mac/Linux

# Установить зависимости
pip install -r requirements.txt

# Настроить переменные окружения
cp .env.example .env
# Заполнить .env

# Применить миграции
alembic upgrade head

# Запустить сервер
uvicorn main:app --reload --port 8000
```

Swagger-документация: http://localhost:8000/docs

## Запуск через Docker

```bash
docker-compose up -d
```

## Переменные окружения

Все переменные описаны в `.env.example`. Основные:

| Переменная | Описание |
|---|---|
| `DATABASE_URL` | PostgreSQL (Neon) |
| `REDIS_URL` | Redis (Upstash, формат `rediss://`) |
| `SECRET_KEY` | Секрет для JWT (мин. 32 символа) |
| `S3_ENDPOINT_URL` | Эндпоинт Supabase Storage |
| `S3_ACCESS_KEY` / `S3_SECRET_KEY` | Ключи Supabase Storage |
| `S3_BUCKET_NAME` | Имя бакета |
| `ALLOWED_ORIGINS` | CORS (домен фронтенда) |

## Модули

| Модуль | Префикс | Описание |
|---|---|---|
| auth | `/api/auth` | Регистрация, логин, JWT, профиль |
| users | `/api/users` | Аватар пользователя |
| listings | `/api/listings` | Объявления, избранное, карта |
| search | `/api/search` | Полнотекстовый поиск, автодополнение |
| chat | `/api/chat` | Чат, WebSocket |
| files | `/api/files` | Загрузка и управление фото |
| admin | `/api/admin` | Модерация, статистика |

## Миграции

```bash
# Создать миграцию
alembic revision --autogenerate -m "описание"

# Применить
alembic upgrade head

# Откатить
alembic downgrade -1
```

## Тесты

```bash
# Все тесты
pytest tests/ -v

# С покрытием
pytest tests/ --cov=app --cov-report=term-missing
```

Тесты используют SQLite in-memory — реальная БД не нужна.

## Celery

Email-уведомления (новые сообщения в чате, смена статуса объявления) отправляются через Celery.
В продакшне Celery worker не запущен — для работы email нужен отдельный сервис с доступом к Redis.

Локальный запуск:

```bash
celery -A core.celery_app worker --loglevel=info
```

> Без запущенного worker API работает полностью — email просто не отправляются.
