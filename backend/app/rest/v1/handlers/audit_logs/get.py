from dataclasses import dataclass
from uuid import UUID

from backend.app.errors import NotFoundError
from backend.app.rest.v1 import dtos
from backend.app.rest.v1.handlers.base import Command, Handler, HandlerType
from backend.app.shared.db.database import Database


class GetAuditLogCommand(Command):
    id: UUID


@dataclass
class GetAuditLogHandler(Handler[GetAuditLogCommand, dtos.AuditLog, None], type_=HandlerType.READ):
    db: Database

    async def __call__(self, cmd: GetAuditLogCommand, _ctx: None = None) -> dtos.AuditLog:
        async with self.db:
            audit_log = (await self.db.gateway.audit_log.get_by_id(cmd.id)).some(NotFoundError())
        return dtos.AuditLog.from_object(audit_log)
