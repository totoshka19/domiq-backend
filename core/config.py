from typing import Optional
from urllib.parse import parse_qs, urlencode, urlparse, urlunparse

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8")

    # Database
    # APP_DATABASE_URL позволяет переопределить DATABASE_URL на платформах,
    # которые блокируют это имя переменной (например, Replit)
    APP_DATABASE_URL: Optional[str] = None
    DATABASE_URL: str = "postgresql+asyncpg://postgres:password@localhost:5432/domiq"

    @property
    def db_url(self) -> str:
        url = self.APP_DATABASE_URL or self.DATABASE_URL

        # Нормализуем схему для asyncpg
        if url.startswith("postgres://"):
            url = "postgresql+asyncpg://" + url[len("postgres://"):]
        elif url.startswith("postgresql://"):
            url = "postgresql+asyncpg://" + url[len("postgresql://"):]

        # Нормализуем параметры SSL: убираем libpq-специфичные, добавляем asyncpg-совместимые
        parsed = urlparse(url)
        params = parse_qs(parsed.query, keep_blank_values=True)

        if "sslmode" in params:
            sslmode = params.pop("sslmode")[0]
            if sslmode == "require" and "ssl" not in params:
                params["ssl"] = ["require"]

        params.pop("channel_binding", None)

        new_query = urlencode({k: v[0] for k, v in params.items()})
        return urlunparse(parsed._replace(query=new_query))

    # Redis
    REDIS_URL: str = "redis://localhost:6379"

    # JWT
    SECRET_KEY: str = "change-me-to-random-32-char-string"
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 30
    REFRESH_TOKEN_EXPIRE_DAYS: int = 7

    # S3-совместимое хранилище (Supabase Storage / Cloudflare R2)
    S3_BUCKET_NAME: str = ""
    S3_ACCESS_KEY: str = ""
    S3_SECRET_KEY: str = ""
    S3_ENDPOINT_URL: str = ""
    S3_REGION: str = "auto"
    # Публичный базовый URL для доступа к файлам (может отличаться от endpoint)
    # Supabase: https://<ref>.supabase.co/storage/v1/object/public
    S3_PUBLIC_URL: str = ""

    # CORS
    ALLOWED_ORIGINS: str = "http://localhost:3000"

    # Email / SMTP (опционально — если не задано, уведомления только логируются)
    SMTP_HOST: Optional[str] = None
    SMTP_PORT: int = 587
    SMTP_USER: Optional[str] = None
    SMTP_PASSWORD: Optional[str] = None
    SMTP_FROM: str = "noreply@domiq.ru"
    ADMIN_EMAIL: Optional[str] = None


settings = Settings()
