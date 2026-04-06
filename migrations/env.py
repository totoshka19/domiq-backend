import asyncio
import sys
from logging.config import fileConfig

from sqlalchemy import engine_from_config, pool
from sqlalchemy.ext.asyncio import create_async_engine

from alembic import context

# Импортируем Base и все модели — Alembic должен их "видеть" для autogenerate
from core.config import settings
from core.base import Base
from app.auth.models import *  # noqa: F401, F403
from app.listings.models import *  # noqa: F401, F403
from app.chat.models import *  # noqa: F401, F403

config = context.config

if config.config_file_name is not None:
    fileConfig(config.config_file_name)

target_metadata = Base.metadata


# ── Режим offline (генерация SQL без подключения к БД) ────────────────────────

def run_migrations_offline() -> None:
    # Для offline-режима всегда используем psycopg2 URL (синтаксис диалекта)
    url = settings.DATABASE_URL.replace(
        "postgresql+asyncpg://", "postgresql+psycopg2://"
    )
    context.configure(
        url=url,
        target_metadata=target_metadata,
        literal_binds=True,
        dialect_opts={"paramstyle": "named"},
    )
    with context.begin_transaction():
        context.run_migrations()


# ── Вспомогательная функция: выполнить миграции в sync-соединении ─────────────

def do_run_migrations(connection) -> None:
    context.configure(connection=connection, target_metadata=target_metadata)
    with context.begin_transaction():
        context.run_migrations()


# ── Режим online — asyncpg (Linux / Mac / CI) ─────────────────────────────────

async def run_async_migrations() -> None:
    """Запускает миграции через asyncpg. Работает на Linux/Mac без psycopg2."""
    engine = create_async_engine(settings.DATABASE_URL, poolclass=pool.NullPool)
    async with engine.begin() as connection:
        await connection.run_sync(do_run_migrations)
    await engine.dispose()


# ── Режим online — psycopg2 (Windows) ────────────────────────────────────────

def run_sync_migrations() -> None:
    """Запускает миграции через psycopg2 (синхронно).
    Нужен на Windows Python 3.14: asyncpg не работает с ProactorEventLoop.
    """
    sync_url = settings.DATABASE_URL.replace(
        "postgresql+asyncpg://", "postgresql+psycopg2://"
    )
    config.set_main_option("sqlalchemy.url", sync_url)
    connectable = engine_from_config(
        config.get_section(config.config_ini_section, {}),
        prefix="sqlalchemy.",
        poolclass=pool.NullPool,
    )
    with connectable.connect() as connection:
        do_run_migrations(connection)


# ── Точка входа ───────────────────────────────────────────────────────────────

def run_migrations_online() -> None:
    if sys.platform == "win32":
        # Windows: asyncpg несовместим с ProactorEventLoop → используем psycopg2
        run_sync_migrations()
    else:
        # Linux / Mac / Docker / CI: asyncpg работает нормально
        asyncio.run(run_async_migrations())


if context.is_offline_mode():
    run_migrations_offline()
else:
    run_migrations_online()
