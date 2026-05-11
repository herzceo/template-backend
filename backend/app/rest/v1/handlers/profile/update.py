from dataclasses import dataclass
from uuid import UUID

from backend.app.errors import NotFoundError
from backend.app.rest.v1 import dtos
from backend.app.rest.v1.handlers.base import Command, Handler, HandlerType
from backend.domain.repos.database import Database


class UpdateProfileCommand(Command):
    user_id: UUID
    display_name: str | None = None
    avatar_url: str | None = None


@dataclass
class UpdateProfileHandler(
    Handler[UpdateProfileCommand, dtos.Profile, None], type_=HandlerType.WRITE
):
    db: Database

    async def __call__(self, cmd: UpdateProfileCommand, _ctx: None = None) -> dtos.Profile:
        async with self.db:
            profile = (await self.db.gateway.profile.get_by_user_id(cmd.user_id)).some(
                NotFoundError(message="Profile not found")
            )
            if cmd.display_name is not None:
                profile.display_name = cmd.display_name
            if cmd.avatar_url is not None:
                profile.avatar_url = cmd.avatar_url
            updated = (await self.db.gateway.profile.update(profile)).some(
                NotFoundError(message="Profile not found")
            )
            await self.db.commit()
        return dtos.Profile.from_object(updated)
