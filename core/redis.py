import redis.asyncio as aioredis

from core.config import settings

_redis: aioredis.Redis | None = None


def get_redis() -> aioredis.Redis:
    global _redis
    if _redis is None:
        _redis = aioredis.from_url(settings.REDIS_URL, decode_responses=True)
    return _redis


async def blacklist_token(token: str, ttl_seconds: int) -> None:
    r = get_redis()
    await r.setex(f"blacklist:{token}", ttl_seconds, "1")


async def is_token_blacklisted(token: str) -> bool:
    r = get_redis()
    return await r.exists(f"blacklist:{token}") == 1
