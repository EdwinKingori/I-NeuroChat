from fastapi import HTTPException, status

from app.core.redis.redis_config import AsyncRedisClient

# Per-IP rate limit on auth endpoints
RATE_LIMIT_MAX = 20          # max requests
RATE_LIMIT_WINDOW = 60       # per 60-second window

# Per-identifier brute-force lockout
BRUTE_FORCE_MAX = 5          # max failed attempts
BRUTE_FORCE_LOCKOUT = 900    # 15-minute lockout


class RateLimiter:

    @staticmethod
    async def check_rate_limit(redis: AsyncRedisClient, ip: str) -> None:
        """Raises 429 if the IP exceeds the auth endpoint rate limit."""
        count = await redis.incr(f"rate_limit:{ip}", ttl_on_create=RATE_LIMIT_WINDOW)
        if count > RATE_LIMIT_MAX:
            raise HTTPException(
                status_code=status.HTTP_429_TOO_MANY_REQUESTS,
                detail="Too many requests. Please slow down.",
            )

    @staticmethod
    async def check_brute_force(redis: AsyncRedisClient, identifier: str) -> None:
        """Raises 429 if the identifier (email/username) is currently locked out."""
        raw = await redis.get_data(f"brute_force:{identifier}")
        count = int(raw) if raw else 0
        if count >= BRUTE_FORCE_MAX:
            raise HTTPException(
                status_code=status.HTTP_429_TOO_MANY_REQUESTS,
                detail=(
                    "Account temporarily locked due to too many failed attempts. "
                    "Try again in 15 minutes."
                ),
            )

    @staticmethod
    async def record_failed_attempt(redis: AsyncRedisClient, identifier: str) -> None:
        """Increment failed login counter, setting TTL on the first failure."""
        await redis.incr(f"brute_force:{identifier}", ttl_on_create=BRUTE_FORCE_LOCKOUT)

    @staticmethod
    async def clear_failed_attempts(redis: AsyncRedisClient, identifier: str) -> None:
        """Clear brute-force counter after a successful login."""
        await redis.delete(f"brute_force:{identifier}")
