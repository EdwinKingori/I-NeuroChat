import aioredis
import json
import logging
from app.core.config import get_settings
from .hmac_security import hmac_key
from typing import AsyncGenerator
settings = get_settings()
logger = logging.getLogger(__name__)


# Configuring central redis client
class AsyncRedisClient:
    """
    Redis client with:
    - Async connection pooling
    - HMA-secured key names
    - TTL support
    - Dependency integration
    - Graceful connection/closure
    """

    def __init__(self):
        self._client: aioredis.Redis | None = None
        self._url = settings.REDIS_URL

    # === Initializing redis connection ===
    async def connect(self) -> None:
        if self._client is not None:
            return

        try:
            self._client = aioredis.from_url(
                self._url,
                encoding="utf-8",
                decode_responses=True,
                socket_connect_timeout=5,
                socket_timeout=5,
                retry_on_timeout=True,
                health_check_interval=30,
            )
            await self._client.ping()
            logger.info("⚡️ Redis connected successfully")
        except Exception as e:
            logger.critical(f"🚫 Failed to connect to Redis: {e}")
            raise

    # === Closing redis connection ===
    async def close(self) -> None:
        if self._client:
            await self._client.close()
            logger.info("Redis connection closed")
            self._client = None

    # Applying HMAC security to prevent key injection/collision
    def _hkey(self, key: str) -> str:
        return hmac_key(key)

    # Retrieving value by key with HMAC
    async def get_data(self, key: str):
        if not self._client:
            await self.connect()
        return await self._client.get(self._hkey(key))

    # Setting/ storing data in  key -> value with an optionl expiration
    async def set_data(self, key: str, value: str, ex: int | None = None):
        if not self._client:
            await self.connect()
        hkey = self._hkey(key)
        return await self._client.set(hkey, value, ex=ex)

    # Deleting key
    async def delete(self, key: str):
        if not self._client:
            await self.connect()
        return await self._client.delete(self._hkey(key))

    # Checking of key exists
    async def exists(self, key: str) -> bool:
        if not self._client:
            await self.connect()
        return await self._client.exists(self._hkey(key)) == 1

    # === Utility: JSON Helpers ===
    async def get_json(self, key: str):
        """Retrieve value and parse JSON. Returns None if missing."""
        raw = await self.get_data(key)
        if not raw:
            return None
        try:
            return json.loads(raw)
        except json.JSONDecodeError:
            logger.exception("Failed to decode JSON for key %s", key)
            return None

    async def set_json(self, key: str, value: dict, ex: int | None = None):
        """Serialize value to JSON and store it."""
        try:
            payload = json.dumps(value)
        except (TypeError, ValueError) as exc:
            logger.exception(
                "Value for set_json is not JSON serializable: %s", exc)
            raise
        return await self.set_data(key, payload, ex=ex)


redis_client = AsyncRedisClient()


# === FastAPI Dependancy ===
async def get_redis() -> AsyncGenerator[AsyncRedisClient, None]:
    """
    Dependency: ensures Redis is connected before yielding.
    To be used in routes: `redis: AsyncRedisClient = Depends(get_redis)`
    """
    await redis_client.connect()
    try:
        yield redis_client
    finally:
        pass
