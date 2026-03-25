from typing import final

from backend.domain.entities.tenant import Tenant
from backend.domain.repos.tenant import TenantRepo

from .base import ImplCRUDSupported


@final
class ImplTenantRepo(ImplCRUDSupported[Tenant], TenantRepo):
    __slots__ = ()
