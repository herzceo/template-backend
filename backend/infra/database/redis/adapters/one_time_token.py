from typing import final
from uuid import UUID

from backend.app.shared.ports.security.one_time_token import OneTimeTokenStore
from backend.app.shared.ports.security.secret_token import SecretTokenGenerator
from backend.infra.database.redis.client import RedisClient
from backend.internal.option import Option

_PREFIX = "ott:"


def _key(purpose: str, token_hash: str) -> str:
    return f"{_PREFIX}{purpose}:{token_hash}"


@final
class ImplRedisOneTimeTokenStore(OneTimeTokenStore):
    __slots__ = ("_hasher", "_redis")

    def __init__(self, redis: RedisClient, hasher: SecretTokenGenerator) -> None:
        self._redis = redis
        self._hasher = hasher

    async def issue(self, purpose: str, user_id: UUID, ttl_seconds: int) -> str:
        raw_token = self._hasher.generate()
        await self._redis.set(
            _key(purpose, self._hasher.hash(raw_token)),
            str(user_id),
            ttl=ttl_seconds,
        )
        return raw_token

    async def consume(self, purpose: str, token: str) -> Option[UUID]:
        key = _key(purpose, self._hasher.hash(token))
        value = await self._redis.get(key)
        if value is None:
            return Option(None)
        # Single-use: drop the key before returning so a replay resolves to None.
        await self._redis.delete(key)
        return Option(UUID(value))
