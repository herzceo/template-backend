from abc import abstractmethod
from typing import Protocol
from uuid import UUID

from backend.internal import Option
from backend.internal.dto import StructDTO


class VerificationEntry(StructDTO):
    code_hash: str
    attempts: int
    created_at: str


class VerificationCodeStore(Protocol):
    @abstractmethod
    async def issue_code(self, user_id: UUID) -> str: ...

    @abstractmethod
    async def verify(self, user_id: UUID, code: str) -> bool: ...

    @abstractmethod
    async def get(self, user_id: UUID) -> Option[VerificationEntry]: ...

    @abstractmethod
    async def delete(self, user_id: UUID) -> None: ...

    @property
    @abstractmethod
    def max_attempts(self) -> int: ...
