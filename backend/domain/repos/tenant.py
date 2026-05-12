from abc import abstractmethod
from typing import Protocol

from backend.domain.entities.tenant import Tenant
from backend.domain.repos.base import CRUDSupported
from backend.internal import Option


class TenantRepo(CRUDSupported[Tenant], Protocol):
    @abstractmethod
    async def get_default(self) -> Option[Tenant]: ...

    @abstractmethod
    async def get_by_app_id(self, app_id: str) -> Option[Tenant]: ...
