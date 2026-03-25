from typing import final

from backend.domain.entities.permission import Permission
from backend.domain.repos.permission import PermissionRepo

from .base import ImplCRUDSupported


@final
class ImplPermissionRepo(ImplCRUDSupported[Permission], PermissionRepo):
    __slots__ = ()
