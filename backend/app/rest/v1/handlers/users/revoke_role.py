from dataclasses import dataclass

from uuid_utils.compat import UUID

from backend.app.rest.v1.handlers.base import Command, Handler, HandlerType
from backend.domain.repos.database import Database


class RevokeRoleCommand(Command):
    user_id: str
    role_id: str


@dataclass
class RevokeRoleHandler(Handler[RevokeRoleCommand, None, None], type_=HandlerType.WRITE):
    db: Database

    async def __call__(self, cmd: RevokeRoleCommand, _ctx: None = None) -> None:
        async with self.db:
            await self.db.gateway.user.revoke_role(UUID(cmd.user_id), UUID(cmd.role_id))
            await self.db.commit()
