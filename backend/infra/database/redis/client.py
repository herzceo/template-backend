from typing import Any, cast, final

from redis.asyncio import Redis, from_url

from backend.infra.database.redis.config import RedisConfig


@final
class RedisClient:
    __slots__ = ("_redis",)

    def __init__(self, config: RedisConfig) -> None:
        self._redis: Redis = from_url(config.url, decode_responses=config.REDIS_DECODE_RESPONSES)

    async def get(self, key: str) -> str | None:
        return cast("str | None", await self._redis.get(key))

    async def set(
        self, key: str, value: str, *, ttl: int | None = None, keepttl: bool = False
    ) -> None:
        """Write ``key``.

        ``keepttl`` overwrites the value while preserving the key's remaining
        expiry — the rewrite of a record that must not have its lifetime
        extended (e.g. an in-flight signup stash).
        """
        await self._redis.set(key, value, ex=ttl, keepttl=keepttl)

    async def delete(self, *keys: str) -> int:
        return cast("int", await self._redis.delete(*keys))

    async def exists(self, key: str) -> bool:
        return cast("int", await self._redis.exists(key)) > 0

    async def incr_fixed_window(self, key: str, window_seconds: int) -> tuple[int, int]:
        """Atomically increment a counter and (on first hit) set its TTL.

        Returns ``(count, ttl_remaining)``. The expiry is set only when absent
        (``nx=True``) so the window does not slide forward on every request.
        """
        async with self._redis.pipeline(transaction=True) as pipe:
            pipe.incr(key)
            pipe.expire(key, window_seconds, nx=True)
            pipe.ttl(key)
            count, _, ttl = await pipe.execute()
        return cast("int", count), cast("int", ttl)

    async def set_hash(self, key: str, mapping: dict[str, Any], *, ttl: int | None = None) -> None:
        await self._redis.hset(key, mapping={k: str(v) for k, v in mapping.items()})  # type: ignore[misc]
        if ttl is not None:
            await self._redis.expire(key, ttl)

    async def get_hash(self, key: str) -> dict[str, str]:
        return cast("dict[str, str]", await self._redis.hgetall(key))  # type: ignore[misc]

    async def get_hash_field(self, key: str, field: str) -> str | None:
        return cast("str | None", await self._redis.hget(key, field))  # type: ignore[misc]

    async def increment_hash_field(self, key: str, field: str, amount: int = 1) -> int:
        return cast("int", await self._redis.hincrby(key, field, amount))  # type: ignore[misc]

    async def close(self) -> None:
        await self._redis.aclose()
