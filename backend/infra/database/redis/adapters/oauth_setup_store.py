from typing import final

import msgspec

from backend.app.shared.ports.security.oauth_setup_store import (
    OAuthSetupSession,
    OAuthSetupStore,
)
from backend.app.shared.ports.security.secret_token import SecretTokenGenerator
from backend.infra.database.redis.client import RedisClient
from backend.internal.option import Option

_PREFIX = "oauth_setup:"


def _key(token_hash: str) -> str:
    return f"{_PREFIX}{token_hash}"


@final
class ImplRedisOAuthSetupStore(OAuthSetupStore):
    __slots__ = ("_hasher", "_redis")

    def __init__(self, redis: RedisClient, hasher: SecretTokenGenerator) -> None:
        self._redis = redis
        self._hasher = hasher

    async def issue(self, session: OAuthSetupSession, ttl_seconds: int) -> str:
        raw_token = self._hasher.generate()
        await self._redis.set(
            _key(self._hasher.hash(raw_token)),
            msgspec.json.encode(session).decode(),
            ttl=ttl_seconds,
        )
        return raw_token

    async def get(self, token: str) -> Option[OAuthSetupSession]:
        return self._decode(await self._redis.get(_key(self._hasher.hash(token))))

    async def update(self, token: str, session: OAuthSetupSession) -> bool:
        key = _key(self._hasher.hash(token))
        if await self._redis.get(key) is None:
            return False
        # keepttl: supplying the email must not extend the setup window.
        await self._redis.set(key, msgspec.json.encode(session).decode(), keepttl=True)
        return True

    async def consume(self, token: str) -> Option[OAuthSetupSession]:
        key = _key(self._hasher.hash(token))
        raw = await self._redis.get(key)
        if raw is None:
            return Option(None)
        await self._redis.delete(key)
        return self._decode(raw)

    @staticmethod
    def _decode(raw: str | None) -> Option[OAuthSetupSession]:
        if raw is None:
            return Option(None)
        return Option(msgspec.json.decode(raw.encode(), type=OAuthSetupSession))
