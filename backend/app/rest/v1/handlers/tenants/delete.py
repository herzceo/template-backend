from dataclasses import dataclass

from uuid_utils.compat import UUID

from backend.app.rest.v1.handlers.base import Command, Handler, HandlerType
from backend.domain.repos.gateway import RepoGateway


class DeleteTenantCommand(Command):
    id: str


@dataclass
class DeleteTenantHandler(Handler[DeleteTenantCommand, None, None], type_=HandlerType.WRITE):
    gateway: RepoGateway

    async def __call__(self, cmd: DeleteTenantCommand, _ctx: None = None) -> None:
        await self.gateway.tenant.delete_by_id(UUID(cmd.id))
        await self.gateway.commiter.commit()
