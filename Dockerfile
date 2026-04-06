FROM python:3.14-slim

WORKDIR /app

# Устанавливаем curl для healthcheck
RUN apt-get update && apt-get install -y --no-install-recommends curl \
    && rm -rf /var/lib/apt/lists/*

# Сначала зависимости — слой кешируется, пока requirements.prod.txt не изменится
# requirements.prod.txt — без psycopg2 (не нужен в API-контейнере) и без dev-пакетов
COPY requirements.prod.txt .
RUN pip install --no-cache-dir -r requirements.prod.txt

# Копируем исходный код
COPY . .

EXPOSE 8000

HEALTHCHECK --interval=30s --timeout=10s --start-period=15s --retries=3 \
    CMD curl -f http://localhost:8000/health || exit 1

CMD ["sh", "-c", "alembic upgrade head && uvicorn main:app --host 0.0.0.0 --port ${PORT:-8000}"]
