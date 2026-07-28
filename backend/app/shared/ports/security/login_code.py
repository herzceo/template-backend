from abc import abstractmethod
from typing import Protocol
from uuid import UUID

from backend.app.shared.ports.security.verification import VerificationEntry
from backend.internal import Option


class LoginCodeStore(Protocol):
    """Email-code ("magic code") login codes.

    Deliberately a distinct port + Redis namespace from ``VerificationCodeStore``
    (email verification) even though the entry shape is shared: the two flows have
    independent lifetimes and attempt counters for the same user.
    """

    @abstractmethod
    async def issue_code(self, user_id: UUID) -> str: ...

    @abstractmethod
    async def verify(self, user_id: UUID, code: str) -> bool: ...

    @abstractmethod
    async def get(self, user_id: UUID) -> Option[VerificationEntry]: ...

    @abstractmethod
    async def delete(self, user_id: UUID) -> None: ...

    @abstractmethod
    async def invalidate(self, user_id: UUID) -> None: ...

    @property
    @abstractmethod
    def max_attempts(self) -> int: ...

    @property
    @abstractmethod
    def ttl_seconds(self) -> int: ...
