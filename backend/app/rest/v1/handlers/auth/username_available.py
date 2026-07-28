from dataclasses import dataclass

from backend.app.errors import InvalidInputError
from backend.app.rest.v1 import dtos
from backend.app.rest.v1.handlers.base import Command, Handler, HandlerType
from backend.app.rest.v1.validation import normalize_username, sanitize_username_chars
from backend.app.shared.db.database import Database


class UsernameAvailabilityCommand(Command):
    username: str


@dataclass
class UsernameAvailabilityHandler(
    Handler[UsernameAvailabilityCommand, dtos.UsernameAvailability, None],
    type_=HandlerType.READ,
):
    """Public inline-validation endpoint for the signup form.

    Runs the exact same sanitizer/validator the signup handler uses, so the form
    can show live feedback that matches what submit would do. Existence disclosure
    is equivalent to the signup 409 — no new information leaks.
    """

    db: Database

    async def __call__(
        self, cmd: UsernameAvailabilityCommand, _ctx: None = None
    ) -> dtos.UsernameAvailability:
        try:
            username = normalize_username(cmd.username)
        except InvalidInputError:
            return dtos.UsernameAvailability(
                available=False,
                reason="invalid",
                sanitized=sanitize_username_chars(cmd.username),
            )
        async with self.db:
            existing = (await self.db.gateway.user.get_by_username(username)).value
        if existing is not None:
            return dtos.UsernameAvailability(available=False, reason="taken", sanitized=username)
        return dtos.UsernameAvailability(available=True, reason="ok", sanitized=username)
