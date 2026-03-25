from dataclasses import dataclass

from uuid_utils.compat import UUID

from backend.app.rest.v1.handlers.base import Command, Handler, HandlerType
from backend.domain.repos.gateway import RepoGateway


class DeleteUserCommand(Command):
    id: str


@dataclass
class DeleteUserHandler(Handler[DeleteUserCommand, None, None], type_=HandlerType.WRITE):
    gateway: RepoGateway

    async def __call__(self, cmd: DeleteUserCommand, _ctx: None = None) -> None:
        await self.gateway.user.delete_by_id(UUID(cmd.id))
        await self.gateway.commiter.commit()
