from functools import cached_property
from typing import final

from sqlalchemy.ext.asyncio import AsyncSession

from backend.domain.repos import RepoGateway

from .asset import ImplAssetRepo
from .audit_log import ImplAuditLogRepo
from .identity import ImplIdentityRepo
from .notification import ImplNotificationRepo
from .permission import ImplPermissionRepo
from .queue import (
    ImplJobEventRepo,
    ImplJobRepo,
    ImplWorkerEventRepo,
    ImplWorkerRepo,
)
from .role import ImplRoleRepo
from .session import ImplSessionRepo
from .tenant import ImplTenantRepo
from .user import ImplUserRepo


@final
class ImplRepoGateway(RepoGateway):
    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    @cached_property
    def user(self) -> ImplUserRepo:
        return ImplUserRepo(self._session)

    @cached_property
    def tenant(self) -> ImplTenantRepo:
        return ImplTenantRepo(self._session)

    @cached_property
    def identity(self) -> ImplIdentityRepo:
        return ImplIdentityRepo(self._session)

    @cached_property
    def role(self) -> ImplRoleRepo:
        return ImplRoleRepo(self._session)

    @cached_property
    def permission(self) -> ImplPermissionRepo:
        return ImplPermissionRepo(self._session)

    @cached_property
    def session_(self) -> ImplSessionRepo:
        return ImplSessionRepo(self._session)

    @cached_property
    def asset(self) -> ImplAssetRepo:
        return ImplAssetRepo(self._session)

    @cached_property
    def notification(self) -> ImplNotificationRepo:
        return ImplNotificationRepo(self._session)

    @cached_property
    def audit_log(self) -> ImplAuditLogRepo:
        return ImplAuditLogRepo(self._session)

    @cached_property
    def job(self) -> ImplJobRepo:
        return ImplJobRepo(self._session)

    @cached_property
    def job_event(self) -> ImplJobEventRepo:
        return ImplJobEventRepo(self._session)

    @cached_property
    def queue_worker(self) -> ImplWorkerRepo:
        return ImplWorkerRepo(self._session)

    @cached_property
    def worker_event(self) -> ImplWorkerEventRepo:
        return ImplWorkerEventRepo(self._session)
