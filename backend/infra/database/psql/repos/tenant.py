from typing import final

from sqlalchemy import select

from backend.domain.entities.tenant import Tenant
from backend.domain.repos.tenant import TenantRepo
from backend.internal import Option

from .base import ImplCRUDSupported


@final
class ImplTenantRepo(ImplCRUDSupported[Tenant], TenantRepo):
    __slots__ = ()

    async def get_default(self) -> Option[Tenant]:
        stmt = select(Tenant).where(Tenant.is_default.is_(True))
        result = await self._session.execute(stmt)
        return Option(result.scalar_one_or_none())
