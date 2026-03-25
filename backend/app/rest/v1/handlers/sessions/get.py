from dataclasses import dataclass

from uuid_utils.compat import UUID

from backend.app.errors import NotFoundError
from backend.app.rest.v1 import dtos
from backend.app.rest.v1.handlers.base import Command, Handler, HandlerType
from backend.domain.repos.gateway import RepoGateway


class GetSessionCommand(Command):
    id: str


@dataclass
class GetSessionHandler(Handler[GetSessionCommand, dtos.Session, None], type_=HandlerType.READ):
    gateway: RepoGateway

    async def __call__(self, cmd: GetSessionCommand, _ctx: None = None) -> dtos.Session:
        session = (await self.gateway.session_.get_by_id(UUID(cmd.id))).some(NotFoundError())
        return dtos.Session.from_object(session)
