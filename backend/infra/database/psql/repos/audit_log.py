from typing import final

from backend.domain.entities.audit_log import AuditLog
from backend.domain.repos.audit_log import AuditLogRepo

from .base import (
    ImplCountSupported,
    ImplCreateSupported,
    ImplGetByIdSupported,
    ImplOffsetPaginationSupported,
)


@final
class ImplAuditLogRepo(
    ImplCreateSupported[AuditLog],
    ImplGetByIdSupported[AuditLog],
    ImplCountSupported[AuditLog],
    ImplOffsetPaginationSupported[AuditLog],
    AuditLogRepo,
):
    __slots__ = ()
