import secrets
from datetime import UTC, datetime
from typing import final
from uuid import UUID

from backend.app.shared.ports.security.secret_token import SecretTokenGenerator
from backend.app.shared.ports.security.verification import VerificationCodeStore, VerificationEntry
from backend.infra.database.redis.adapters.config import VerificationConfig
from backend.infra.database.redis.client import RedisClient
from backend.internal.option import Option

_PREFIX = "verification:"


def _key(user_id: UUID) -> str:
    return f"{_PREFIX}{user_id}"


def _generate_code() -> str:
    return str(secrets.randbelow(900000) + 100000)


@final
class ImplVerificationCodeStore(VerificationCodeStore):
    __slots__ = ("_config", "_hasher", "_redis")

    def __init__(
        self, redis: RedisClient, hasher: SecretTokenGenerator, config: VerificationConfig
    ) -> None:
        self._redis = redis
        self._hasher = hasher
        self._config = config

    async def issue_code(self, user_id: UUID) -> str:
        raw_code = _generate_code()
        entry = VerificationEntry(
            code_hash=self._hasher.hash(raw_code),
            attempts=0,
            created_at=datetime.now(UTC).isoformat(),
        )
        await self._redis.set_hash(
            _key(user_id),
            dict(entry.to_builtins()),
            ttl=self._config.VERIFICATION_TTL_SECONDS,
        )
        return raw_code

    async def verify(self, user_id: UUID, code: str) -> bool:
        entry = (await self.get(user_id)).value
        if entry is None:
            return False

        if self._hasher.hash(code) == entry.code_hash:
            await self.delete(user_id)
            return True

        await self._redis.increment_hash_field(_key(user_id), "attempts")
        return False

    async def get(self, user_id: UUID) -> Option[VerificationEntry]:
        data = await self._redis.get_hash(_key(user_id))
        if not data:
            return Option(None)
        return Option(VerificationEntry.from_builtins(data))

    async def delete(self, user_id: UUID) -> None:
        await self._redis.delete(_key(user_id))

    async def invalidate(self, user_id: UUID) -> None:
        await self.delete(user_id)

    @property
    def max_attempts(self) -> int:
        return self._config.VERIFICATION_MAX_ATTEMPTS

    @property
    def ttl_seconds(self) -> int:
        return self._config.VERIFICATION_TTL_SECONDS
