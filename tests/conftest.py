import pytest
import pytest_asyncio
from httpx import ASGITransport, AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine

from core.base import Base
from core.database import get_db

# Импортируем все модели чтобы Base знал о них
# ВАЖНО: эти импорты должны быть до `from main import app`,
# иначе `import app.*` перепишет имя `app` на пакет, а не FastAPI-инстанс
import app.auth.models  # noqa: F401
import app.listings.models  # noqa: F401
import app.chat.models  # noqa: F401

from main import app  # noqa: E402 — намеренно после model-импортов
from core.limiter import limiter


@pytest.fixture(autouse=True)
def disable_rate_limiting():
    """Отключить rate limiting в тестах."""
    limiter.enabled = False
    yield
    limiter.enabled = True


@pytest.fixture(autouse=True)
def celery_eager(monkeypatch):
    """Запускать Celery-задачи синхронно без брокера Redis."""
    from core.celery_app import celery
    celery.conf.update(task_always_eager=True, task_eager_propagates=False)


@pytest.fixture(autouse=True)
def mock_redis(monkeypatch):
    """Мок Redis — в тестах нет реального Redis."""
    import core.redis as redis_module

    blacklist: set[str] = set()

    async def fake_blacklist_token(token: str, ttl_seconds: int) -> None:
        blacklist.add(token)

    async def fake_is_blacklisted(token: str) -> bool:
        return token in blacklist

    monkeypatch.setattr(redis_module, "blacklist_token", fake_blacklist_token)
    monkeypatch.setattr(redis_module, "is_token_blacklisted", fake_is_blacklisted)

    import app.auth.router as auth_router
    monkeypatch.setattr(auth_router, "blacklist_token", fake_blacklist_token)
    monkeypatch.setattr(auth_router, "is_token_blacklisted", fake_is_blacklisted)

TEST_DATABASE_URL = "sqlite+aiosqlite:///:memory:"


@pytest_asyncio.fixture(scope="function")
async def db_engine():
    engine = create_async_engine(TEST_DATABASE_URL, echo=False)
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    yield engine
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)
    await engine.dispose()


@pytest_asyncio.fixture(scope="function")
async def db_session(db_engine):
    session_factory = async_sessionmaker(db_engine, expire_on_commit=False)
    async with session_factory() as session:
        yield session


@pytest_asyncio.fixture(scope="function")
async def client(db_session: AsyncSession):
    async def override_get_db():
        yield db_session

    app.dependency_overrides[get_db] = override_get_db
    async with AsyncClient(
        transport=ASGITransport(app=app),
        base_url="http://test",
    ) as ac:
        yield ac
    app.dependency_overrides.clear()


# ── Вспомогательные фикстуры ───────────────────────────────────────────────────

@pytest_asyncio.fixture
async def registered_user(client: AsyncClient) -> dict:
    """Зарегистрированный пользователь с ролью user."""
    resp = await client.post("/api/auth/register", json={
        "email": "user@test.com",
        "password": "password123",
        "full_name": "Test User",
        "role": "user",
    })
    assert resp.status_code == 201
    return resp.json()


@pytest_asyncio.fixture
async def user_token(client: AsyncClient, registered_user: dict) -> str:
    resp = await client.post("/api/auth/login", json={
        "email": "user@test.com",
        "password": "password123",
    })
    assert resp.status_code == 200
    return resp.json()["access_token"]


@pytest_asyncio.fixture
async def registered_agent(client: AsyncClient) -> dict:
    """Зарегистрированный пользователь с ролью agent."""
    resp = await client.post("/api/auth/register", json={
        "email": "agent@test.com",
        "password": "password123",
        "full_name": "Test Agent",
        "role": "agent",
    })
    assert resp.status_code == 201
    return resp.json()


@pytest_asyncio.fixture
async def agent_token(client: AsyncClient, registered_agent: dict) -> str:
    resp = await client.post("/api/auth/login", json={
        "email": "agent@test.com",
        "password": "password123",
    })
    assert resp.status_code == 200
    return resp.json()["access_token"]


@pytest_asyncio.fixture
async def registered_admin(client: AsyncClient) -> dict:
    """Зарегистрированный пользователь с ролью admin."""
    resp = await client.post("/api/auth/register", json={
        "email": "admin@test.com",
        "password": "password123",
        "full_name": "Test Admin",
        "role": "admin",
    })
    assert resp.status_code == 201
    return resp.json()


@pytest_asyncio.fixture
async def admin_token(client: AsyncClient, registered_admin: dict) -> str:
    resp = await client.post("/api/auth/login", json={
        "email": "admin@test.com",
        "password": "password123",
    })
    assert resp.status_code == 200
    return resp.json()["access_token"]


@pytest_asyncio.fixture
async def listing(client: AsyncClient, agent_token: str) -> dict:
    """Созданное объявление от агента."""
    resp = await client.post(
        "/api/listings",
        json={
            "title": "Тестовая квартира",
            "description": "Хорошая квартира в центре",
            "deal_type": "sale",
            "property_type": "apartment",
            "price": "5000000",
            "area": "45.5",
            "rooms": 2,
            "floor": 3,
            "floors_total": 9,
            "address": "ул. Тестовая, 1",
            "city": "Москва",
        },
        headers={"Authorization": f"Bearer {agent_token}"},
    )
    assert resp.status_code == 201
    return resp.json()
