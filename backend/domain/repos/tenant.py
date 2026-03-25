from typing import Protocol

from backend.domain.entities.tenant import Tenant
from backend.domain.repos.base import CRUDSupported


class TenantRepo(CRUDSupported[Tenant], Protocol): ...
