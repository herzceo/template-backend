from __future__ import annotations

import secrets
from dataclasses import dataclass, field
from typing import final

from backend.app.shared.ports.security.oauth_setup_store import OAuthSetupSession
from backend.internal import Option


@final
@dataclass
class MockOAuthSetupStore:
    """In-memory ``OAuthSetupStore`` keyed by a generated raw token."""

    _sessions: dict[str, OAuthSetupSession] = field(default_factory=dict)

    async def issue(self, session: OAuthSetupSession, ttl_seconds: int) -> str:  # noqa: ARG002
        token = secrets.token_urlsafe(24)
        self._sessions[token] = session
        return token

    async def get(self, token: str) -> Option[OAuthSetupSession]:
        return Option(self._sessions.get(token))

    async def update(self, token: str, session: OAuthSetupSession) -> bool:
        if token not in self._sessions:
            return False
        self._sessions[token] = session
        return True

    async def consume(self, token: str) -> Option[OAuthSetupSession]:
        return Option(self._sessions.pop(token, None))
