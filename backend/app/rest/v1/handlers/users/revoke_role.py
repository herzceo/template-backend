from dataclasses import dataclass
from uuid import UUID

from backend.app.rest.v1.handlers.base import Command, Handler, HandlerType
from backend.domain.repos.database import Database


class RevokeRoleCommand(Command):
    user_id: UUID
    role_id: UUID


@dataclass
class RevokeRoleHandler(Handler[RevokeRoleCommand, None, None], type_=HandlerType.WRITE):
    db: Database

    async def __call__(self, cmd: RevokeRoleCommand, _ctx: None = None) -> None:
        async with self.db:
            await self.db.gateway.user.revoke_role(cmd.user_id, cmd.role_id)
            await self.db.commit()
