from dataclasses import dataclass
from uuid import UUID

from backend.app.errors import InvalidInputError
from backend.app.rest.v1.handlers.base import Command, Handler, HandlerType
from backend.app.shared.db.database import Database

_ALLOWED_REACTIONS: frozenset[str | None] = frozenset({"useful", "not_useful", None})


class ReactCommand(Command):
    notification_id: UUID
    user_id: UUID
    reaction: str | None


@dataclass
class ReactHandler(Handler[ReactCommand, None, None], type_=HandlerType.WRITE):
    db: Database

    async def __call__(self, cmd: ReactCommand, _ctx: None = None) -> None:
        if cmd.reaction not in _ALLOWED_REACTIONS:
            raise InvalidInputError(
                message=(
                    f"reaction must be one of useful, not_useful, or null (got {cmd.reaction!r})"
                ),
                details={"reaction": cmd.reaction},
            )
        async with self.db:
            await self.db.gateway.notification.set_reaction(
                cmd.notification_id, cmd.user_id, cmd.reaction
            )
            await self.db.commit()
