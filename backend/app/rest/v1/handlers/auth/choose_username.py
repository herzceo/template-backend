from dataclasses import dataclass
from uuid import UUID

from backend.app.errors import AlreadyExistsError, ConflictError, NotFoundError
from backend.app.rest.v1 import dtos
from backend.app.rest.v1.handlers.base import Command, Handler, HandlerType
from backend.app.rest.v1.validation import normalize_username
from backend.app.shared.db.database import Database


class ChooseUsernameCommand(Command):
    user_id: UUID
    username: str


@dataclass
class ChooseUsernameHandler(
    Handler[ChooseUsernameCommand, dtos.User, None], type_=HandlerType.WRITE
):
    """One-time username selection for a fresh OAuth account.

    Allowed only while the account's username is still the auto-generated preset
    (``username_confirmed is False``). Once confirmed the username is immutable —
    there is no change-username endpoint anywhere.
    """

    db: Database

    async def __call__(self, cmd: ChooseUsernameCommand, _ctx: None = None) -> dtos.User:
        username = normalize_username(cmd.username)
        async with self.db:
            user = (await self.db.gateway.user.get_by_id(cmd.user_id)).some(NotFoundError())
            if user.username_confirmed:
                raise ConflictError(
                    message="Your username is already set and can't be changed",
                    code="username_locked",
                )
            if username != user.username:
                (await self.db.gateway.user.get_by_username(username)).none(
                    AlreadyExistsError(message="Username already taken", code="username_taken")
                )
            user.username = username
            user.username_confirmed = True
            (await self.db.gateway.user.update(user)).some(RuntimeError("Failed to set username"))
            await self.db.commit()
        return dtos.User.from_object(user)
