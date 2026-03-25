from abc import abstractmethod
from typing import Protocol
from uuid import UUID

from backend.domain.entities.session import Session
from backend.domain.repos.base import CRUDSupported
from backend.internal import Option


class SessionRepo(CRUDSupported[Session], Protocol):
    @abstractmethod
    async def get_by_token_hash(self, token_hash: str) -> Option[Session]: ...

    @abstractmethod
    async def delete_by_user_id(self, user_id: UUID) -> None: ...
