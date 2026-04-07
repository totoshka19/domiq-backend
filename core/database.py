from typing import AsyncGenerator

from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine

from core.base import Base  # noqa: F401 — re-export for convenience
from core.config import settings

engine = create_async_engine(
    settings.db_url,
    echo=True,
    connect_args={"prepared_statement_cache_size": 0},
)
AsyncSessionLocal = async_sessionmaker(engine, expire_on_commit=False)


async def get_db() -> AsyncGenerator[AsyncSession, None]:
    async with AsyncSessionLocal() as session:
        yield session
