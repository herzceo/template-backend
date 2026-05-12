from uuid import UUID

from litestar import Controller, get

from backend.app.rest.v1 import dtos
from backend.app.rest.v1.handlers import audit_logs
from backend.internal.di import Depends


class AuditLogsController(Controller):
    path = "/audit-logs"
    tags = ("Audit Logs",)

    @get("/")
    async def list_audit_logs(
        self,
        handler: Depends[audit_logs.ListAuditLogsHandler],
        offset: int = 0,
        limit: int = 50,
    ) -> dtos.PaginatedResponse[dtos.AuditLog]:
        return await handler(audit_logs.ListAuditLogsCommand(offset=offset, limit=limit))

    @get("/{id:str}")
    async def get_audit_log(
        self,
        id: str,
        handler: Depends[audit_logs.GetAuditLogHandler],
    ) -> dtos.AuditLog:
        return await handler(audit_logs.GetAuditLogCommand(id=UUID(id)))
