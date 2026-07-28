from typing import final

from backend.app.shared.ports.security.rate_limiter import RateLimitDecision, RateLimiter
from backend.infra.database.redis.client import RedisClient

_PREFIX = "ratelimit:"


@final
class ImplRedisRateLimiter(RateLimiter):
    __slots__ = ("_redis",)

    def __init__(self, redis: RedisClient) -> None:
        self._redis = redis

    async def hit(self, key: str, *, limit: int, window_seconds: int) -> RateLimitDecision:
        count, ttl = await self._redis.incr_fixed_window(f"{_PREFIX}{key}", window_seconds)
        if count > limit:
            return RateLimitDecision(allowed=False, retry_after=ttl if ttl > 0 else window_seconds)
        return RateLimitDecision(allowed=True, retry_after=0)
