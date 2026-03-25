from dataclasses import dataclass

from uuid_utils.compat import UUID

from backend.app.errors import NotFoundError
from backend.app.rest.v1 import dtos
from backend.app.rest.v1.handlers.base import Command, Handler, HandlerType
from backend.domain.repos.gateway import RepoGateway


class GetAuditLogCommand(Command):
    id: str


@dataclass
class GetAuditLogHandler(Handler[GetAuditLogCommand, dtos.AuditLog, None], type_=HandlerType.READ):
    gateway: RepoGateway

    async def __call__(self, cmd: GetAuditLogCommand, _ctx: None = None) -> dtos.AuditLog:
        audit_log = (await self.gateway.audit_log.get_by_id(UUID(cmd.id))).some(NotFoundError())
        return dtos.AuditLog.from_object(audit_log)
