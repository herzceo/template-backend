from __future__ import annotations

import secrets
from dataclasses import dataclass, field
from typing import TYPE_CHECKING, final

from backend.internal import Option

if TYPE_CHECKING:
    from uuid import UUID


@final
@dataclass
class MockOneTimeTokenStore:
    """In-memory ``OneTimeTokenStore`` — single-use, purpose-scoped tokens.

    A token minted under one purpose can never be consumed under another, and a
    successful consume can never succeed twice.
    """

    # token -> (purpose, user_id)
    _tokens: dict[str, tuple[str, UUID]] = field(default_factory=dict)

    async def issue(self, purpose: str, user_id: UUID, ttl_seconds: int) -> str:  # noqa: ARG002
        token = secrets.token_urlsafe(24)
        self._tokens[token] = (purpose, user_id)
        return token

    async def consume(self, purpose: str, token: str) -> Option[UUID]:
        entry = self._tokens.get(token)
        if entry is None or entry[0] != purpose:
            return Option(None)
        del self._tokens[token]
        return Option(entry[1])
