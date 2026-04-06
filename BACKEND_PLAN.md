# Domiq — Подробный план разработки Backend

> Стек: Python 3.12 · FastAPI 0.135 · PostgreSQL · SQLAlchemy 2.0 · Alembic · Redis · Celery · S3

---

## Содержание

1. [Шаг 1 — Подготовка окружения](#шаг-1--подготовка-окружения)
2. [Шаг 2 — Инициализация проекта](#шаг-2--инициализация-проекта)
3. [Шаг 3 — База данных и миграции](#шаг-3--база-данных-и-миграции)
4. [Шаг 4 — Модуль Auth](#шаг-4--модуль-auth)
5. [Шаг 5 — Модуль Listings](#шаг-5--модуль-listings)
6. [Шаг 6 — Модуль Files (S3)](#шаг-6--модуль-files-s3)
7. [Шаг 7 — Модуль Search](#шаг-7--модуль-search)
8. [Шаг 8 — Модуль Chat (WebSocket)](#шаг-8--модуль-chat-websocket)
9. [Шаг 9 — Модуль Notifications (Celery)](#шаг-9--модуль-notifications-celery)
10. [Шаг 10 — Админ-панель](#шаг-10--админ-панель)
11. [Шаг 11 — Тесты](#шаг-11--тесты)
12. [Шаг 12 — Docker и деплой](#шаг-12--docker-и-деплой)

---

## Шаг 1 — Подготовка окружения

### 1.1 Установка инструментов
- [ ] Установить Python 3.12: https://python.org/downloads
- [ ] Установить Docker Desktop: https://docker.com/products/docker-desktop
- [ ] Установить VS Code + расширения: Python, Pylance, Docker, REST Client
- [ ] Установить git (если не установлен)

### 1.2 Создание виртуального окружения
```bash
cd D:\PetProjects\Domiq\domiq-backend

# Создать виртуальное окружение
python -m venv .venv

# Активировать (Windows)
.venv\Scripts\activate

# Активировать (Mac/Linux)
source .venv/bin/activate
```

### 1.3 Установка зависимостей
```bash
pip install fastapi==0.135.3
pip install "uvicorn[standard]"
pip install sqlalchemy==2.0.49
pip install alembic==1.18.4
pip install psycopg2-binary          # драйвер PostgreSQL
pip install asyncpg                  # асинхронный драйвер PostgreSQL
pip install pydantic==2.11.3
pip install "pydantic[email]"
pip install pydantic-settings
pip install python-jose==3.3.0
pip install "passlib[bcrypt]==1.7.4"
pip install python-multipart
pip install celery==5.6.3
pip install redis
pip install boto3                    # S3 / Yandex Object Storage
pip install httpx                    # HTTP-клиент для тестов
pip install pytest
pip install pytest-asyncio
pip install python-dotenv

# Сохранить все зависимости
pip freeze > requirements.txt
```

---

## Шаг 2 — Инициализация проекта

### 2.1 Структура папок
Создать следующую структуру вручную или командами:

```
domiq-backend/
├── app/
│   ├── __init__.py
│   ├── auth/
│   │   ├── __init__.py
│   │   ├── router.py        # маршруты: /auth/register, /auth/login
│   │   ├── models.py        # SQLAlchemy модель User
│   │   ├── schemas.py       # Pydantic схемы запросов/ответов
│   │   ├── service.py       # бизнес-логика: хэш пароля, проверка
│   │   └── dependencies.py  # get_current_user, role_required
│   ├── listings/
│   │   ├── __init__.py
│   │   ├── router.py
│   │   ├── models.py
│   │   ├── schemas.py
│   │   └── service.py
│   ├── search/
│   │   ├── __init__.py
│   │   ├── router.py
│   │   └── service.py
│   ├── chat/
│   │   ├── __init__.py
│   │   ├── router.py        # WebSocket эндпоинт
│   │   ├── models.py
│   │   └── service.py
│   ├── files/
│   │   ├── __init__.py
│   │   ├── router.py
│   │   └── service.py       # загрузка в S3
│   ├── notifications/
│   │   ├── __init__.py
│   │   └── tasks.py         # Celery задачи
│   └── admin/
│       ├── __init__.py
│       ├── router.py
│       └── service.py
├── core/
│   ├── __init__.py
│   ├── config.py            # настройки через pydantic-settings
│   ├── database.py          # подключение к БД, сессия
│   ├── security.py          # JWT: создание и верификация токенов
│   └── celery_app.py        # инициализация Celery
├── migrations/              # создаётся Alembic
│   ├── env.py
│   └── versions/
├── tests/
│   ├── __init__.py
│   ├── conftest.py
│   ├── test_auth.py
│   ├── test_listings.py
│   └── test_search.py
├── .env                     # переменные окружения (не в git!)
├── .env.example             # шаблон без секретов (в git)
├── .gitignore
├── alembic.ini
├── docker-compose.yml
├── Dockerfile
├── requirements.txt
└── main.py                  # точка входа
```

### 2.2 Файл main.py
```python
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.auth.router import router as auth_router
from app.listings.router import router as listings_router
from app.search.router import router as search_router
from app.chat.router import router as chat_router
from app.files.router import router as files_router
from app.admin.router import router as admin_router

app = FastAPI(
    title="Domiq API",
    version="1.0.0",
    description="Маркетплейс недвижимости"
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000"],  # фронтенд
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(auth_router,     prefix="/api/auth",     tags=["Auth"])
app.include_router(listings_router, prefix="/api/listings", tags=["Listings"])
app.include_router(search_router,   prefix="/api/search",   tags=["Search"])
app.include_router(chat_router,     prefix="/api/chat",     tags=["Chat"])
app.include_router(files_router,    prefix="/api/files",    tags=["Files"])
app.include_router(admin_router,    prefix="/api/admin",    tags=["Admin"])

@app.get("/")
def root():
    return {"status": "ok", "project": "Domiq API"}
```

### 2.3 Файл core/config.py
```python
from pydantic_settings import BaseSettings

class Settings(BaseSettings):
    # БД — Neon (prod) или локальный PostgreSQL (dev)
    DATABASE_URL: str

    # Redis — Upstash (prod) или локальный Redis (dev)
    REDIS_URL: str = "redis://localhost:6379"

    # JWT
    SECRET_KEY: str
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 30
    REFRESH_TOKEN_EXPIRE_DAYS: int = 7

    # Cloudflare R2 (S3-совместимый)
    S3_BUCKET_NAME: str
    S3_ACCESS_KEY: str
    S3_SECRET_KEY: str
    S3_ENDPOINT_URL: str  # https://<account-id>.r2.cloudflarestorage.com

    # CORS
    ALLOWED_ORIGINS: str = "http://localhost:3000"

    class Config:
        env_file = ".env"

settings = Settings()
```

### 2.4 Файл .env.example
```env
# --- Локальная разработка ---
DATABASE_URL=postgresql+asyncpg://postgres:password@localhost:5432/domiq

# --- Продакшн: Neon ---
# DATABASE_URL=postgresql+asyncpg://user:pass@ep-xxx.neon.tech/domiq?sslmode=require

# --- Локальный Redis (dev) ---
REDIS_URL=redis://localhost:6379

# --- Продакшн: Upstash Redis (обязательно rediss:// с двумя s) ---
# REDIS_URL=rediss://default:pass@xxx.upstash.io:6379

# JWT
SECRET_KEY=change-me-to-random-32-char-string
ALGORITHM=HS256
ACCESS_TOKEN_EXPIRE_MINUTES=30
REFRESH_TOKEN_EXPIRE_DAYS=7

# Cloudflare R2
S3_BUCKET_NAME=domiq-files
S3_ACCESS_KEY=your-r2-access-key-id
S3_SECRET_KEY=your-r2-secret-access-key
S3_ENDPOINT_URL=https://your-account-id.r2.cloudflarestorage.com

# CORS
ALLOWED_ORIGINS=http://localhost:3000,https://domiq.vercel.app
```

### 2.5 Файл .gitignore
```
.venv/
__pycache__/
*.pyc
.env
*.egg-info/
.pytest_cache/
```

---

## Шаг 3 — База данных и миграции

### 3.1 Запуск PostgreSQL через Docker
```bash
# Запустить только PostgreSQL для разработки
docker run -d \
  --name domiq-postgres \
  -e POSTGRES_USER=postgres \
  -e POSTGRES_PASSWORD=password \
  -e POSTGRES_DB=domiq \
  -p 5432:5432 \
  postgres:16
```

### 3.2 Подключение к БД (core/database.py)
```python
from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker, AsyncSession
from sqlalchemy.orm import DeclarativeBase
from core.config import settings

engine = create_async_engine(settings.DATABASE_URL, echo=True)
AsyncSessionLocal = async_sessionmaker(engine, expire_on_commit=False)

class Base(DeclarativeBase):
    pass

async def get_db() -> AsyncSession:
    async with AsyncSessionLocal() as session:
        yield session
```

### 3.3 Инициализация Alembic
```bash
alembic init migrations
```

Отредактировать `migrations/env.py` — подключить Base и все модели:
```python
from core.database import Base
from app.auth.models import User          # обязательно импортировать все модели
from app.listings.models import Listing, Photo
from app.chat.models import Message

target_metadata = Base.metadata
```

### 3.4 ER-схема базы данных

**Таблица users**
| Поле | Тип | Описание |
|---|---|---|
| id | UUID (PK) | уникальный ID |
| email | VARCHAR(255) UNIQUE | email |
| phone | VARCHAR(20) UNIQUE NULL | телефон |
| hashed_password | VARCHAR | хэш пароля |
| role | ENUM(user, agent, admin) | роль |
| full_name | VARCHAR(255) | имя |
| avatar_url | VARCHAR NULL | ссылка на фото |
| is_active | BOOLEAN DEFAULT true | активен ли |
| created_at | TIMESTAMP | дата регистрации |

**Таблица listings**
| Поле | Тип | Описание |
|---|---|---|
| id | UUID (PK) | уникальный ID |
| owner_id | UUID (FK → users) | владелец |
| title | VARCHAR(255) | заголовок |
| description | TEXT | описание |
| deal_type | ENUM(sale, rent) | продажа или аренда |
| property_type | ENUM(apartment, house, commercial, land) | тип |
| price | DECIMAL(12,2) | цена |
| currency | VARCHAR(3) DEFAULT 'RUB' | валюта |
| area | DECIMAL(8,2) | площадь м² |
| rooms | INTEGER NULL | количество комнат |
| floor | INTEGER NULL | этаж |
| floors_total | INTEGER NULL | всего этажей |
| address | VARCHAR(500) | адрес строкой |
| city | VARCHAR(100) | город |
| district | VARCHAR(100) NULL | район |
| latitude | DECIMAL(9,6) NULL | координаты |
| longitude | DECIMAL(9,6) NULL | координаты |
| status | ENUM(active, archived, sold) | статус |
| is_moderated | BOOLEAN DEFAULT false | прошло ли модерацию |
| created_at | TIMESTAMP | дата создания |
| updated_at | TIMESTAMP | дата обновления |

**Таблица listing_photos**
| Поле | Тип | Описание |
|---|---|---|
| id | UUID (PK) | уникальный ID |
| listing_id | UUID (FK → listings) | объявление |
| url | VARCHAR(500) | URL в S3 |
| order | INTEGER DEFAULT 0 | порядок отображения |
| is_main | BOOLEAN DEFAULT false | главное фото |

**Таблица favorites**
| Поле | Тип | Описание |
|---|---|---|
| id | UUID (PK) | уникальный ID |
| user_id | UUID (FK → users) | пользователь |
| listing_id | UUID (FK → listings) | объявление |
| created_at | TIMESTAMP | дата добавления |

**Таблица conversations**
| Поле | Тип | Описание |
|---|---|---|
| id | UUID (PK) | уникальный ID |
| listing_id | UUID (FK → listings) | объявление |
| buyer_id | UUID (FK → users) | покупатель |
| seller_id | UUID (FK → users) | продавец |
| created_at | TIMESTAMP | дата создания |

**Таблица messages**
| Поле | Тип | Описание |
|---|---|---|
| id | UUID (PK) | уникальный ID |
| conversation_id | UUID (FK → conversations) | чат |
| sender_id | UUID (FK → users) | отправитель |
| text | TEXT | текст |
| is_read | BOOLEAN DEFAULT false | прочитано |
| created_at | TIMESTAMP | дата |

### 3.5 Создание и применение миграций
```bash
# Создать первую миграцию
alembic revision --autogenerate -m "initial tables"

# Применить миграцию
alembic upgrade head

# Откатить последнюю миграцию (если нужно)
alembic downgrade -1
```

---

## Шаг 4 — Модуль Auth

### 4.1 Что реализовать
- [ ] Регистрация по email + пароль
- [ ] Регистрация по телефону (опционально)
- [ ] Логин → возврат access + refresh токенов
- [ ] Обновление токена по refresh token
- [ ] Выход (logout — инвалидация refresh токена)
- [ ] Получение текущего пользователя (`GET /auth/me`)
- [ ] Обновление профиля (`PATCH /auth/me`)

### 4.2 Эндпоинты
| Метод | URL | Описание | Доступ |
|---|---|---|---|
| POST | /api/auth/register | Регистрация | Все |
| POST | /api/auth/login | Логин | Все |
| POST | /api/auth/refresh | Обновить токен | Все |
| POST | /api/auth/logout | Выйти | Авторизован |
| GET | /api/auth/me | Профиль | Авторизован |
| PATCH | /api/auth/me | Редактировать профиль | Авторизован |

### 4.3 Ключевые концепции

**Хэширование пароля (core/security.py):**
```python
from passlib.context import CryptContext
from jose import JWTError, jwt
from datetime import datetime, timedelta
from core.config import settings

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

def hash_password(password: str) -> str:
    return pwd_context.hash(password)

def verify_password(plain: str, hashed: str) -> bool:
    return pwd_context.verify(plain, hashed)

def create_access_token(data: dict) -> str:
    expire = datetime.utcnow() + timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
    return jwt.encode({**data, "exp": expire}, settings.SECRET_KEY, settings.ALGORITHM)
```

**Зависимость get_current_user (auth/dependencies.py):**
```python
from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/api/auth/login")

async def get_current_user(token: str = Depends(oauth2_scheme), db = Depends(get_db)):
    # декодировать JWT, найти пользователя в БД
    ...

def role_required(role: str):
    async def checker(user = Depends(get_current_user)):
        if user.role != role:
            raise HTTPException(status_code=403, detail="Forbidden")
        return user
    return checker
```

---

## Шаг 5 — Модуль Listings

### 5.1 Что реализовать
- [ ] Создание объявления (только agent/admin)
- [ ] Редактирование своего объявления
- [ ] Удаление (архивирование) объявления
- [ ] Получение списка объявлений с пагинацией
- [ ] Получение одного объявления по ID
- [ ] Добавление в избранное
- [ ] Удаление из избранного
- [ ] Получение избранных объявлений пользователя

### 5.2 Эндпоинты
| Метод | URL | Описание | Доступ |
|---|---|---|---|
| GET | /api/listings | Список объявлений | Все |
| GET | /api/listings/{id} | Одно объявление | Все |
| POST | /api/listings | Создать объявление | agent, admin |
| PATCH | /api/listings/{id} | Обновить объявление | Владелец, admin |
| DELETE | /api/listings/{id} | Архивировать | Владелец, admin |
| POST | /api/listings/{id}/favorite | Добавить в избранное | Авторизован |
| DELETE | /api/listings/{id}/favorite | Убрать из избранного | Авторизован |
| GET | /api/listings/favorites | Мои избранные | Авторизован |
| GET | /api/listings/my | Мои объявления | Авторизован |

### 5.3 Пагинация и фильтрация
```python
# listings/router.py
@router.get("/")
async def get_listings(
    page: int = 1,
    limit: int = 20,
    city: str | None = None,
    deal_type: str | None = None,       # sale | rent
    property_type: str | None = None,   # apartment | house | ...
    price_min: float | None = None,
    price_max: float | None = None,
    rooms: int | None = None,
    area_min: float | None = None,
    area_max: float | None = None,
    sort_by: str = "created_at",        # price | area | created_at
    sort_order: str = "desc",           # asc | desc
    db: AsyncSession = Depends(get_db)
):
    ...
```

---

## Шаг 6 — Модуль Files (S3)

### 6.1 Что реализовать
- [ ] Загрузка одного фото → получение URL
- [ ] Загрузка нескольких фото сразу (до 20 штук)
- [ ] Удаление фото из S3 + из БД
- [ ] Изменение порядка фото
- [ ] Назначение главного фото

### 6.2 Эндпоинты
| Метод | URL | Описание | Доступ |
|---|---|---|---|
| POST | /api/files/upload | Загрузить фото | Авторизован |
| DELETE | /api/files/{photo_id} | Удалить фото | Владелец |
| PATCH | /api/files/reorder | Изменить порядок | Владелец |

### 6.3 Загрузка через Celery (асинхронно)
```python
# notifications/tasks.py
from core.celery_app import celery

@celery.task
def upload_photo_to_s3(file_data: bytes, filename: str, listing_id: str):
    """Загрузка фото в Cloudflare R2 в фоне"""
    import boto3
    from core.config import settings

    # R2 совместим с boto3 — только endpoint и region отличаются
    s3 = boto3.client(
        "s3",
        endpoint_url=settings.S3_ENDPOINT_URL,        # https://<id>.r2.cloudflarestorage.com
        aws_access_key_id=settings.S3_ACCESS_KEY,
        aws_secret_access_key=settings.S3_SECRET_KEY,
        region_name="auto",                            # обязательно для R2
    )
    s3.put_object(
        Bucket=settings.S3_BUCKET_NAME,
        Key=f"listings/{listing_id}/{filename}",
        Body=file_data,
        ContentType="image/jpeg"
    )
    # обновить запись в БД с публичным URL фото
    # URL формат: https://pub-xxx.r2.dev/listings/{listing_id}/{filename}
```

---

## Шаг 7 — Модуль Search

### 7.1 Что реализовать
- [ ] Полнотекстовый поиск по title + description + address
- [ ] Комбинация поиска с фильтрами из Listings
- [ ] Поиск объявлений в заданном радиусе (по координатам)
- [ ] Автодополнение по городу / адресу

### 7.2 Эндпоинты
| Метод | URL | Описание | Доступ |
|---|---|---|---|
| GET | /api/search | Поиск объявлений | Все |
| GET | /api/search/autocomplete | Подсказки по вводу | Все |

### 7.3 Полнотекстовый поиск в PostgreSQL
```python
# search/service.py
from sqlalchemy import func, cast
from sqlalchemy.dialects.postgresql import TSVECTOR

async def search_listings(query: str, db: AsyncSession):
    search_vector = func.to_tsvector("russian",
        func.concat_ws(" ",
            Listing.title,
            Listing.description,
            Listing.address
        )
    )
    search_query = func.plainto_tsquery("russian", query)

    result = await db.execute(
        select(Listing)
        .where(search_vector.op("@@")(search_query))
        .order_by(func.ts_rank(search_vector, search_query).desc())
    )
    return result.scalars().all()
```

---

## Шаг 8 — Модуль Chat (WebSocket)

### 8.1 Что реализовать
- [ ] Создание чата между покупателем и продавцом по объявлению
- [ ] Отправка сообщений через WebSocket
- [ ] История сообщений (REST)
- [ ] Отметка сообщений как прочитанных
- [ ] Список всех чатов пользователя

### 8.2 Эндпоинты
| Метод | URL | Описание | Доступ |
|---|---|---|---|
| POST | /api/chat/conversations | Начать чат | Авторизован |
| GET | /api/chat/conversations | Мои чаты | Авторизован |
| GET | /api/chat/conversations/{id}/messages | История | Авторизован |
| WS | /api/chat/ws/{conversation_id} | WebSocket | Авторизован |

### 8.3 WebSocket соединение
```python
# chat/router.py
from fastapi import WebSocket, WebSocketDisconnect

class ConnectionManager:
    def __init__(self):
        # conversation_id → список подключённых WebSocket
        self.active: dict[str, list[WebSocket]] = {}

    async def connect(self, ws: WebSocket, conversation_id: str):
        await ws.accept()
        self.active.setdefault(conversation_id, []).append(ws)

    async def broadcast(self, message: str, conversation_id: str):
        for connection in self.active.get(conversation_id, []):
            await connection.send_text(message)

manager = ConnectionManager()

@router.websocket("/ws/{conversation_id}")
async def chat_ws(ws: WebSocket, conversation_id: str):
    await manager.connect(ws, conversation_id)
    try:
        while True:
            data = await ws.receive_text()
            # сохранить в БД
            # отправить всем участникам чата
            await manager.broadcast(data, conversation_id)
    except WebSocketDisconnect:
        manager.active[conversation_id].remove(ws)
```

---

## Шаг 9 — Модуль Notifications (Celery)

### 9.1 Что реализовать
- [ ] Уведомление на email при новом сообщении в чате
- [ ] Уведомление при изменении статуса объявления
- [ ] Отложенная обработка загрузки фото
- [ ] Уведомление администратору о новом объявлении на модерацию

### 9.2 Celery (core/celery_app.py)
```python
from celery import Celery
from core.config import settings

celery = Celery(
    "domiq",
    broker=settings.REDIS_URL,
    backend=settings.REDIS_URL,
)

celery.conf.update(
    task_serializer="json",
    result_serializer="json",
    timezone="Europe/Moscow",
)
```

### 9.3 Запуск Celery Worker
```bash
celery -A core.celery_app worker --loglevel=info
```

---

## Шаг 10 — Админ-панель

### 10.1 Что реализовать
- [ ] Список всех пользователей с фильтрацией
- [ ] Блокировка / разблокировка пользователя
- [ ] Список всех объявлений (включая неактивные)
- [ ] Модерация объявлений (approve / reject)
- [ ] Статистика: кол-во объявлений, пользователей, чатов

### 10.2 Эндпоинты
| Метод | URL | Описание | Доступ |
|---|---|---|---|
| GET | /api/admin/users | Все пользователи | admin |
| PATCH | /api/admin/users/{id}/block | Заблокировать | admin |
| GET | /api/admin/listings | Все объявления | admin |
| PATCH | /api/admin/listings/{id}/approve | Одобрить | admin |
| PATCH | /api/admin/listings/{id}/reject | Отклонить | admin |
| GET | /api/admin/stats | Статистика | admin |

---

## Шаг 11 — Тесты

### 11.1 Конфигурация (tests/conftest.py)
```python
import pytest
from httpx import AsyncClient, ASGITransport
from main import app

@pytest.fixture
async def client():
    async with AsyncClient(
        transport=ASGITransport(app=app),
        base_url="http://test"
    ) as ac:
        yield ac
```

### 11.2 Что покрыть тестами (минимум)
- [ ] Регистрация: успех, дубль email, слабый пароль
- [ ] Логин: успех, неверный пароль, несуществующий пользователь
- [ ] Создание объявления: с токеном, без токена
- [ ] Получение списка объявлений с фильтрами
- [ ] Поиск по тексту
- [ ] Добавление/удаление из избранного
- [ ] Доступ к admin-эндпоинтам без роли admin

### 11.3 Запуск тестов
```bash
pytest tests/ -v
pytest tests/ -v --tb=short   # краткий вывод ошибок
pytest tests/test_auth.py -v  # только тесты авторизации
```

---

## Шаг 12 — Docker и деплой

### 12.1 Dockerfile
```dockerfile
FROM python:3.12-slim

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000"]
```

### 12.2 docker-compose.yml
```yaml
version: "3.9"

services:
  api:
    build: .
    ports:
      - "8000:8000"
    env_file: .env
    depends_on:
      - postgres
      - redis

  postgres:
    image: postgres:16
    environment:
      POSTGRES_USER: postgres
      POSTGRES_PASSWORD: password
      POSTGRES_DB: domiq
    volumes:
      - postgres_data:/var/lib/postgresql/data
    ports:
      - "5432:5432"

  redis:
    image: redis:7-alpine
    ports:
      - "6379:6379"

  celery_worker:
    build: .
    command: celery -A core.celery_app worker --loglevel=info
    env_file: .env
    depends_on:
      - redis
      - postgres

volumes:
  postgres_data:
```

### 12.3 Запуск всего стека
```bash
# Запустить все сервисы
docker-compose up -d

# Применить миграции
docker-compose exec api alembic upgrade head

# Проверить логи
docker-compose logs -f api

# Остановить
docker-compose down
```

### 12.4 Swagger-документация
После запуска доступна по адресу:
- **Swagger UI:** http://localhost:8000/docs
- **ReDoc:** http://localhost:8000/redoc

---

## Порядок выполнения (рекомендуемый)

```
Шаг 1 → Шаг 2 → Шаг 3 → Шаг 4 → Шаг 12 (docker-compose) →
Шаг 5 → Шаг 6 → Шаг 7 → Шаг 8 → Шаг 9 → Шаг 10 → Шаг 11
```

**Почему именно так:**
- Docker поднять рано (Шаг 12 частично) — чтобы сразу была PostgreSQL и Redis
- Auth делать первым — все остальные модули зависят от пользователя
- Listings делать вторым — Search зависит от существующих объявлений
- Chat и Notifications в конце — самые сложные части

---

## Шаг 13 — Деплой на Render + Neon + Upstash + R2

### 13.1 Neon — создание базы данных
1. Зарегистрироваться на neon.tech (без карты)
2. Создать проект `domiq`, регион Frankfurt или Paris
3. Скопировать строку подключения вида:
   `postgresql+asyncpg://user:pass@ep-xxx.eu-central-1.aws.neon.tech/domiq?sslmode=require`
4. Вставить в переменную `DATABASE_URL` на Render

### 13.2 Upstash — создание Redis
1. Зарегистрироваться на upstash.com
2. Создать базу данных Redis, регион EU-West
3. Скопировать `UPSTASH_REDIS_REST_URL` → преобразовать в `rediss://`
4. Вставить в переменную `REDIS_URL` на Render

### 13.3 Cloudflare R2 — создание бакета
1. Зарегистрироваться на cloudflare.com
2. Перейти в R2 Object Storage → Create bucket → `domiq-files`
3. Создать API Token с правами Object Read & Write
4. Включить публичный доступ к бакету (для URL фотографий)
5. Вставить ключи в переменные `S3_*` на Render

### 13.4 Render — деплой бэкенда
1. Зарегистрироваться на render.com → Connect GitHub
2. **Web Service** (FastAPI):
   - Repository: domiq-backend
   - Branch: main
   - Build: `pip install -r requirements.txt`
   - Start: `uvicorn main:app --host 0.0.0.0 --port $PORT`
   - Add Health Check: `/health`
3. **Background Worker** (Celery):
   - Тот же репозиторий, тип: Background Worker
   - Start: `celery -A core.celery_app worker --loglevel=info`
4. В обоих сервисах добавить все переменные из `.env.example`
5. После деплоя применить миграции:
   ```bash
   # Через Render Shell или локально с prod DATABASE_URL
   alembic upgrade head
   ```

### 13.5 Vercel — деплой фронтенда (domiq-frontend)
1. Подключить репозиторий domiq-frontend
2. Framework Preset: Vite
3. Добавить переменную `VITE_API_URL=https://domiq-backend.onrender.com/api`

### 13.6 Важно: Render засыпает на бесплатном плане
Сервис засыпает после 15 минут неактивности. Для MVP это нормально.
Чтобы избежать cold start — добавить `/health` эндпоинт и мониторинг через UptimeRobot (бесплатно):
- Создать аккаунт на uptimerobot.com
- Добавить HTTP-монитор на `https://ваш-сервис.onrender.com/health`
- Интервал: 5 минут — сервис не будет засыпать

---

*Создано для проекта Domiq · Апрель 2026*
