from abc import abstractmethod
from typing import Protocol
from uuid import UUID

from backend.internal import Option

# Purposes namespace one-time tokens so a token minted for one flow can never be
# consumed by another. Kept here so issuer and consumer agree on the literal.
OTT_PURPOSE_SIGNUP_SETUP = "signup_setup"
OTT_PURPOSE_PASSWORD_RESET = "password_reset"
# Short-lived proof-of-identity minted after a password/re-OAuth step-up. Consumed
# by the sensitive-change endpoints (change email / change password).
OTT_PURPOSE_REAUTH = "reauth"


class OneTimeTokenStore(Protocol):
    @abstractmethod
    async def issue(self, purpose: str, user_id: UUID, ttl_seconds: int) -> str:
        """Mint a single-use token bound to ``user_id`` under ``purpose``.

        Returns the raw token (the caller embeds it in a link or hands it back to
        the client). Only its hash is persisted.
        """
        ...

    @abstractmethod
    async def consume(self, purpose: str, token: str) -> Option[UUID]:
        """Atomically resolve ``token`` to its ``user_id`` and invalidate it.

        Returns ``Option(None)`` when the token is unknown, already consumed, or
        expired. A successful consume can never succeed twice.
        """
        ...
