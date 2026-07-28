from __future__ import annotations

import secrets
from dataclasses import dataclass, field
from typing import TYPE_CHECKING, final

from backend.app.shared.ports.security.verification import VerificationEntry
from backend.internal import Option

if TYPE_CHECKING:
    from uuid import UUID


@final
@dataclass
class MockVerificationCodeStore:
    _codes: dict[UUID, str] = field(default_factory=dict)
    _attempts: dict[UUID, int] = field(default_factory=dict)

    async def issue_code(self, user_id: UUID) -> str:
        code = secrets.token_hex(3).upper()
        self._codes[user_id] = code
        self._attempts[user_id] = 0
        return code

    async def verify(self, user_id: UUID, code: str) -> bool:
        self._attempts[user_id] = self._attempts.get(user_id, 0) + 1
        return self._codes.get(user_id) == code

    async def get(self, user_id: UUID) -> Option[VerificationEntry]:
        code = self._codes.get(user_id)
        if code is None:
            return Option(None)
        return Option(
            VerificationEntry(
                code_hash=code,
                attempts=self._attempts.get(user_id, 0),
                created_at="",
            )
        )

    async def delete(self, user_id: UUID) -> None:
        self._codes.pop(user_id, None)
        self._attempts.pop(user_id, None)

    async def invalidate(self, user_id: UUID) -> None:
        await self.delete(user_id)

    @property
    def max_attempts(self) -> int:
        return 5

    @property
    def ttl_seconds(self) -> int:
        return 600

    def get_code(self, user_id: UUID) -> str | None:
        return self._codes.get(user_id)
