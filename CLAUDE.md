# Domiq Backend — инструкции для Claude Code

## О проекте
Маркетплейс недвижимости. Модульный монолит на FastAPI.
Каждый модуль изолирован: auth, listings, search, chat, files, notifications, admin.

---

## Стек

### Локальная разработка
- Python 3.12
- FastAPI 0.135.3
- PostgreSQL + SQLAlchemy 2.0.49 (async) + Alembic 1.18.4
- Redis + Celery 5.6.3
- Pydantic v2
- pytest + httpx для тестов

### Продакшн-инфраструктура (все бесплатно)
| Слой | Сервис | Лимит |
|---|---|---|
| База данных | **Neon** (serverless PostgreSQL) | 100 CU-ч/мес, 0.5 ГБ |
| Бэкенд API | **Render** (FastAPI) | 750 ч/мес, 512 МБ RAM |
| Фоновые задачи | **Render** (Celery worker) | отдельный сервис |
| Redis | **Upstash** (serverless Redis) | 10 000 команд/день |
| Файлы / фото | **Cloudflare R2** | 10 ГБ, 1M запросов/мес |
| Фронтенд | **Vercel** (domiq-frontend) | без ограничений для SPA |

> Vercel используется ТОЛЬКО для фронтенда.
> Бэкенд на Vercel не деплоится: нет WebSocket, нет Celery, таймаут 10 сек.

---

## Команды

### Запуск
```bash
# Запустить только API (dev)
uvicorn main:app --reload --port 8000

# Запустить весь стек через Docker
docker-compose up -d

# Swagger-документация
open http://localhost:8000/docs
```

### База данных
```bash
# Создать миграцию
alembic revision --autogenerate -m "описание изменений"

# Применить миграции
alembic upgrade head

# Откатить последнюю миграцию
alembic downgrade -1

# Посмотреть историю миграций
alembic history
```

### Celery
```bash
# Запустить воркер
celery -A core.celery_app worker --loglevel=info

# Запустить воркер с мониторингом (Flower)
celery -A core.celery_app flower
```

### Тесты
```bash
# Все тесты
pytest tests/ -v

# Один модуль
pytest tests/test_auth.py -v

# С покрытием
pytest tests/ --cov=app --cov-report=term-missing
```

### Виртуальное окружение
```bash
# Активировать (Windows)
.venv\Scripts\activate

# Активировать (Mac/Linux)
source .venv/bin/activate

# Обновить зависимости
pip freeze > requirements.txt
```

---

## Архитектура и правила кода

### Структура модуля
Каждый модуль в `app/` содержит:
- `router.py` — FastAPI роутер, только маршруты, никакой бизнес-логики
- `models.py` — SQLAlchemy модели
- `schemas.py` — Pydantic схемы (суффиксы: `Create`, `Update`, `Response`)
- `service.py` — вся бизнес-логика и работа с БД
- `dependencies.py` — зависимости (только в auth)

### Правила написания кода

**Async везде:**
```python
# ПРАВИЛЬНО
async def get_listing(id: UUID, db: AsyncSession = Depends(get_db)):
    return await listing_service.get_by_id(db, id)

# НЕПРАВИЛЬНО — никогда не использовать sync SQLAlchemy
def get_listing(id: UUID, db: Session = Depends(get_db)):
    ...
```

**UUID для всех PK:**
```python
import uuid
id: Mapped[UUID] = mapped_column(primary_key=True, default=uuid.uuid4)
```

**Pydantic схемы — три суффикса:**
```python
class ListingCreate(BaseModel): ...    # входные данные для создания
class ListingUpdate(BaseModel): ...    # входные данные для обновления (все поля Optional)
class ListingResponse(BaseModel): ...  # то, что возвращаем клиенту
    model_config = ConfigDict(from_attributes=True)
```

**Роли через dependency:**
```python
# Только agent и admin могут создавать объявления
@router.post("/")
async def create(
    data: ListingCreate,
    current_user = Depends(role_required("agent"))
):
    ...
```

**Сервисный слой:**
```python
# router.py — только роутинг
@router.get("/{id}", response_model=ListingResponse)
async def get_listing(id: UUID, db: AsyncSession = Depends(get_db)):
    return await listing_service.get_by_id(db, id)

# service.py — вся логика
async def get_by_id(db: AsyncSession, id: UUID) -> Listing:
    result = await db.execute(select(Listing).where(Listing.id == id))
    listing = result.scalar_one_or_none()
    if not listing:
        raise HTTPException(status_code=404, detail="Listing not found")
    return listing
```

**Формат ошибок — всегда через HTTPException:**
```python
raise HTTPException(status_code=404, detail="Listing not found")
raise HTTPException(status_code=403, detail="You don't have permission")
raise HTTPException(status_code=400, detail="Email already registered")
```

---

## База данных

### Модели — обязательные поля
```python
from sqlalchemy.orm import Mapped, mapped_column
from sqlalchemy import func
import uuid

class BaseModel(Base):
    __abstract__ = True
    id: Mapped[uuid.UUID] = mapped_column(primary_key=True, default=uuid.uuid4)
    created_at: Mapped[datetime] = mapped_column(server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(
        server_default=func.now(), onupdate=func.now()
    )
```

### Сессия — только через Depends
```python
# ПРАВИЛЬНО
async def some_endpoint(db: AsyncSession = Depends(get_db)):
    ...

# НЕПРАВИЛЬНО — не создавать сессию вручную в роутерах
async def some_endpoint():
    async with AsyncSessionLocal() as db:  # только в сервисах, не в роутерах
        ...
```

### Миграции — правила
- Одна миграция = одно логическое изменение
- Название миграции по-английски: `add_phone_to_users`, `create_listings_table`
- Всегда проверять автосгенерированную миграцию перед применением
- Никогда не редактировать уже применённые миграции

---

## Безопасность

### Пароли
```python
# ПРАВИЛЬНО — bcrypt через passlib
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")
hashed = pwd_context.hash(password)

# НЕПРАВИЛЬНО — никогда не хранить пароль в открытом виде
user.password = password
```

### JWT
- `access_token` — живёт 30 минут
- `refresh_token` — живёт 7 дней, хранится в Redis
- Никогда не класть чувствительные данные в payload токена (только `user_id` и `role`)

### Переменные окружения
- Все секреты только в `.env` (в .gitignore!)
- Использовать `pydantic-settings` для загрузки
- `.env.example` с пустыми значениями — в git

---

## Тесты

### Структура теста
```python
# Всегда проверять 4 случая для каждого защищённого эндпоинта:
async def test_create_listing_success(client, agent_token): ...      # 201
async def test_create_listing_unauthorized(client): ...              # 401
async def test_create_listing_forbidden(client, user_token): ...     # 403
async def test_create_listing_invalid_data(client, agent_token): ... # 422
```

### Фикстуры из conftest.py
- `client` — AsyncClient с тестовой БД
- `user_token` — JWT токен пользователя с ролью `user`
- `agent_token` — JWT токен пользователя с ролью `agent`
- `admin_token` — JWT токен пользователя с ролью `admin`

---

## Что не делать

- Не писать бизнес-логику в `router.py`
- Не делать синхронные запросы к БД (`Session` вместо `AsyncSession`)
- Не хранить секреты в коде или комментариях
- Не создавать миграции с именем `auto` (всегда давать осмысленное имя)
- Не возвращать SQLAlchemy модели напрямую — всегда через Pydantic `Response` схему
- Не делать N+1 запросы — использовать `joinedload` или `selectinload`
- Не игнорировать типизацию — все функции должны иметь type hints

---

## Деплой

### Переменные окружения (.env для прода)
```env
# Neon — строку подключения берём из консоли Neon
DATABASE_URL=postgresql+asyncpg://user:pass@ep-xxx.neon.tech/domiq?sslmode=require

# Upstash — берём UPSTASH_REDIS_REST_URL и конвертируем в redis://
REDIS_URL=rediss://default:pass@xxx.upstash.io:6379

# Cloudflare R2
S3_BUCKET_NAME=domiq-files
S3_ACCESS_KEY=your-r2-access-key
S3_SECRET_KEY=your-r2-secret-key
S3_ENDPOINT_URL=https://<account-id>.r2.cloudflarestorage.com

# JWT
SECRET_KEY=your-secret-key-min-32-chars
ALGORITHM=HS256
ACCESS_TOKEN_EXPIRE_MINUTES=30
REFRESH_TOKEN_EXPIRE_DAYS=7

# CORS — домен фронтенда на Vercel
ALLOWED_ORIGINS=https://domiq.vercel.app,http://localhost:3000
```

### Render — настройка сервисов
На Render создаём два сервиса из одного репозитория:

**Сервис 1 — FastAPI (Web Service)**
- Build Command: `pip install -r requirements.txt`
- Start Command: `uvicorn main:app --host 0.0.0.0 --port $PORT`
- Environment: все переменные из .env выше

**Сервис 2 — Celery Worker (Background Worker)**
- Build Command: `pip install -r requirements.txt`
- Start Command: `celery -A core.celery_app worker --loglevel=info`
- Environment: те же переменные

### Neon — подключение
```python
# core/database.py — для продакшна обязательно sslmode=require
DATABASE_URL = "postgresql+asyncpg://...@ep-xxx.neon.tech/domiq?sslmode=require"
```

### Upstash Redis — подключение
```python
# Upstash работает только через TLS, используем rediss:// (с двумя s)
REDIS_URL = "rediss://default:pass@xxx.upstash.io:6379"
```

### Cloudflare R2 — подключение (S3-совместимый)
```python
# files/service.py — R2 совместим с boto3, только endpoint другой
import boto3
s3 = boto3.client(
    "s3",
    endpoint_url=settings.S3_ENDPOINT_URL,  # https://<id>.r2.cloudflarestorage.com
    aws_access_key_id=settings.S3_ACCESS_KEY,
    aws_secret_access_key=settings.S3_SECRET_KEY,
    region_name="auto",  # обязательно для R2
)
```

### Health check эндпоинт (для Render)
Render проверяет живость сервиса через GET /health. Добавить в main.py:
```python
@app.get("/health")
def health():
    return {"status": "ok"}
```

### Автодеплой
Render автоматически деплоит при пуше в ветку `main`.
Для превью-окружений — создать отдельную ветку `staging`.

---



Все коммиты в проекте следуют спецификации [Conventional Commits 1.0.0](https://www.conventionalcommits.org).

### Формат
```
<тип>(<область>): <описание>

[тело — необязательно]

[футер — необязательно]
```

### Типы
| Тип | Когда использовать |
|---|---|
| `feat` | Новый эндпоинт, новая функциональность |
| `fix` | Исправление бага |
| `refactor` | Рефакторинг без изменения поведения |
| `test` | Добавление или исправление тестов |
| `docs` | Документация (README, комментарии) |
| `chore` | Зависимости, конфиги, тулинг |
| `ci` | GitHub Actions, CI/CD |
| `perf` | Оптимизация производительности |
| `style` | Форматирование, нет изменений логики |
| `build` | Docker, requirements.txt |
| `revert` | Откат предыдущего коммита |

### Области (scope) — модули проекта
`auth` · `listings` · `search` · `chat` · `files` · `notifications` · `admin` · `core` · `deps` · `docker` · `migrations`

### Язык коммитов
Описание коммита — **только на русском языке**. Тип и область — английские (это часть стандарта).

### Правила описания
- Повелительное наклонение: "добавить", "исправить" — не "добавлено", "исправлено"
- Строчные буквы, без точки в конце
- Не длиннее 72 символов в первой строке
- Никогда не добавлять `Co-Authored-By` — ни в тело, ни в футер

### Примеры для Domiq
```
feat(auth): добавить эндпоинт обновления JWT токена
fix(listings): исправить пагинацию — неверный total count
feat(search): реализовать полнотекстовый поиск через PostgreSQL FTS
refactor(chat): вынести WebSocket менеджер в отдельный класс
test(auth): добавить тесты для зависимости role_required
chore(deps): обновить SQLAlchemy до 2.0.49
build(docker): добавить сервис celery worker в docker-compose
perf(listings): добавить GIN-индекс по полям city и deal_type
```

### Breaking change
Если изменяется существующий API — добавить `!` и футер:
```
feat(auth)!: заменить username на email в запросе логина

BREAKING CHANGE: эндпоинт логина теперь требует поле 'email' вместо 'username'
```

### Использовать скилл `/commit`
Вместо ручного написания — запустить `/commit` и Claude проанализирует изменения и предложит правильное сообщение на русском без лишних футеров.

---

## Полезные ссылки
- FastAPI docs: https://fastapi.tiangolo.com
- SQLAlchemy 2.0 async: https://docs.sqlalchemy.org/en/20/orm/extensions/asyncio.html
- Alembic: https://alembic.sqlalchemy.org
- Pydantic v2: https://docs.pydantic.dev/latest
- Celery: https://docs.celeryq.dev
