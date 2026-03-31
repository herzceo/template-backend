from dataclasses import dataclass

from uuid_utils.compat import UUID

from backend.app.errors import NotFoundError
from backend.app.rest.v1 import dtos
from backend.app.rest.v1.handlers.base import Command, Handler, HandlerType
from backend.domain.repos.database import Database


class GetSessionCommand(Command):
    id: str


@dataclass
class GetSessionHandler(Handler[GetSessionCommand, dtos.Session, None], type_=HandlerType.READ):
    db: Database

    async def __call__(self, cmd: GetSessionCommand, _ctx: None = None) -> dtos.Session:
        async with self.db:
            session = (await self.db.gateway.session_.get_by_id(UUID(cmd.id))).some(NotFoundError())
        return dtos.Session.from_object(session)
