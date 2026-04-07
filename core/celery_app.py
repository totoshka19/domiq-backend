from celery import Celery

from core.config import settings


def _redis_url_with_ssl(url: str) -> str:
    if url.startswith("rediss://") and "ssl_cert_reqs" not in url:
        sep = "&" if "?" in url else "?"
        return f"{url}{sep}ssl_cert_reqs=CERT_NONE"
    return url


_broker_url = _redis_url_with_ssl(settings.REDIS_URL)

celery = Celery(
    "domiq",
    broker=_broker_url,
    backend=_broker_url,
)

celery.conf.update(
    task_serializer="json",
    result_serializer="json",
    accept_content=["json"],
    timezone="Europe/Moscow",
    enable_utc=True,
)
