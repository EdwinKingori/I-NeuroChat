
from typing import Callable, Any, Awaitable

from app.core.logging.route_logger import get_route_logger
from app.core.redis.redis_config import AsyncRedisClient

logger = get_route_logger("cache.helpers")


async def fetch_from_cache_or_db(
    *,
    redis: AsyncRedisClient,
    redis_key: str,
    db_fetch_callable: Callable[[], Awaitable[Any]],
    ttl: int = 300,
):
    """
    Redis-first read-through cache.

    Returns:
    - (data, source)
      source ∈ {"Redis Cache", "PostgreSQL DB"}
    """

    cached = await redis.get_json(redis_key)
    if cached is not None:
        logger.info("⚡ Cache HIT | %s", redis_key)
        return cached, "Redis Cache"

    logger.info("❌ Cache MISS | %s → PostgreSQL", redis_key)

    data = await db_fetch_callable()

    if data is not None:
        await redis.set_json(redis_key, data, ex=ttl)
        logger.info("📦 Cached | %s (ttl=%ss)", redis_key, ttl)

    return data, "PostgreSQL DB"
