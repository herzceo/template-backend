from abc import abstractmethod
from typing import Protocol
from uuid import UUID

from backend.domain.entities.identity import Identity
from backend.domain.enums import IdentityProvider
from backend.domain.repos.base import CRUDSupported
from backend.internal import Option


class IdentityRepo(CRUDSupported[Identity], Protocol):
    @abstractmethod
    async def get_by_provider_subject(
        self, provider: IdentityProvider, provider_subject_id: str
    ) -> Option[Identity]: ...

    @abstractmethod
    async def list_by_user_id(self, user_id: UUID) -> list[Identity]: ...

    @abstractmethod
    async def delete_by_user_and_provider(
        self, user_id: UUID, provider: IdentityProvider
    ) -> None: ...
