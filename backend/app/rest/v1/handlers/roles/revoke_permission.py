from dataclasses import dataclass

from uuid_utils.compat import UUID

from backend.app.rest.v1.handlers.base import Command, Handler, HandlerType
from backend.domain.repos.gateway import RepoGateway


class RevokePermissionCommand(Command):
    role_id: str
    permission_id: str


@dataclass
class RevokePermissionHandler(
    Handler[RevokePermissionCommand, None, None], type_=HandlerType.WRITE
):
    gateway: RepoGateway

    async def __call__(self, cmd: RevokePermissionCommand, _ctx: None = None) -> None:
        await self.gateway.role.revoke_permission(UUID(cmd.role_id), UUID(cmd.permission_id))
        await self.gateway.commiter.commit()
