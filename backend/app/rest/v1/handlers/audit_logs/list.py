from dataclasses import dataclass

from backend.app.rest.v1 import dtos
from backend.app.rest.v1.handlers.base import Command, Handler, HandlerType
from backend.app.shared.db.database import Database


class ListAuditLogsCommand(Command):
    offset: int = 0
    limit: int = 50


@dataclass
class ListAuditLogsHandler(
    Handler[ListAuditLogsCommand, dtos.PaginatedResponse[dtos.AuditLog], None],
    type_=HandlerType.READ,
):
    db: Database

    async def __call__(
        self, cmd: ListAuditLogsCommand, _ctx: None = None
    ) -> dtos.PaginatedResponse[dtos.AuditLog]:
        async with self.db:
            items = await self.db.gateway.audit_log.list_with_offset(
                offset=cmd.offset, limit=cmd.limit
            )
            total = await self.db.gateway.audit_log.count()
        return dtos.PaginatedResponse(
            items=[dtos.AuditLog.from_object(i) for i in items],
            total=total,
            offset=cmd.offset,
            limit=cmd.limit,
        )
