from dataclasses import dataclass
from uuid import UUID

from backend.app.errors import NotFoundError
from backend.app.rest.v1 import dtos
from backend.app.rest.v1.handlers.base import Command, Handler, HandlerType
from backend.domain.repos.database import Database


class GetProfileCommand(Command):
    user_id: UUID


@dataclass
class GetProfileHandler(Handler[GetProfileCommand, dtos.Profile, None], type_=HandlerType.READ):
    db: Database

    async def __call__(self, cmd: GetProfileCommand, _ctx: None = None) -> dtos.Profile:
        async with self.db:
            profile = (await self.db.gateway.profile.get_by_user_id(cmd.user_id)).some(
                NotFoundError(message="Profile not found")
            )
            return dtos.Profile.from_object(profile)
