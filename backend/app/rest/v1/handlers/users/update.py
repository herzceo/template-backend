from dataclasses import dataclass
from uuid import UUID

from backend.app.errors import NotFoundError
from backend.app.rest.v1 import dtos
from backend.app.rest.v1.handlers.base import Command, Handler, HandlerType
from backend.app.rest.v1.validation import normalize_email
from backend.app.shared.db.database import Database


class UpdateUserCommand(Command):
    id: UUID
    email: str | None = None


@dataclass
class UpdateUserHandler(Handler[UpdateUserCommand, dtos.User, None], type_=HandlerType.WRITE):
    db: Database

    async def __call__(self, cmd: UpdateUserCommand, _ctx: None = None) -> dtos.User:
        async with self.db:
            entity = (await self.db.gateway.user.get_by_id(cmd.id)).some(NotFoundError())
            if cmd.email is not None:
                entity.email = normalize_email(cmd.email)
            updated = (await self.db.gateway.user.update(entity)).some(NotFoundError())
            await self.db.commit()
        return dtos.User.from_object(updated)
