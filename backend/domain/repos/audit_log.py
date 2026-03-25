from typing import Protocol

from backend.domain.entities.audit_log import AuditLog
from backend.domain.repos.base import (
    CountSupported,
    CreateSupported,
    GetByIdSupported,
    OffsetPaginationSupported,
)


class AuditLogRepo(
    CreateSupported[AuditLog],
    GetByIdSupported[AuditLog],
    CountSupported[AuditLog],
    OffsetPaginationSupported[AuditLog],
    Protocol,
): ...
