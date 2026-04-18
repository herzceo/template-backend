from abc import abstractmethod
from typing import Protocol

from .asset import AssetRepo
from .audit_log import AuditLogRepo
from .identity import IdentityRepo
from .notification import NotificationRepo
from .permission import PermissionRepo
from .role import RoleRepo
from .session import SessionRepo
from .tenant import TenantRepo
from .user import UserRepo


class RepoGateway(Protocol):
    @property
    @abstractmethod
    def user(self) -> UserRepo: ...

    @property
    @abstractmethod
    def tenant(self) -> TenantRepo: ...

    @property
    @abstractmethod
    def identity(self) -> IdentityRepo: ...

    @property
    @abstractmethod
    def role(self) -> RoleRepo: ...

    @property
    @abstractmethod
    def permission(self) -> PermissionRepo: ...

    @property
    @abstractmethod
    def session_(self) -> SessionRepo: ...

    @property
    @abstractmethod
    def asset(self) -> AssetRepo: ...

    @property
    @abstractmethod
    def notification(self) -> NotificationRepo: ...

    @property
    @abstractmethod
    def audit_log(self) -> AuditLogRepo: ...
