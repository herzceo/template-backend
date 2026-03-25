from typing import Protocol

from backend.domain.entities.permission import Permission
from backend.domain.repos.base import CRUDSupported


class PermissionRepo(CRUDSupported[Permission], Protocol): ...
