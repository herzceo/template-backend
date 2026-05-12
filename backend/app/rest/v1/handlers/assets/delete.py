from dataclasses import dataclass
from uuid import UUID

from backend.app.rest.v1.handlers.base import Command, Handler, HandlerType
from backend.app.shared.db.database import Database


class DeleteAssetCommand(Command):
    id: UUID


@dataclass
class DeleteAssetHandler(Handler[DeleteAssetCommand, None, None], type_=HandlerType.WRITE):
    db: Database

    async def __call__(self, cmd: DeleteAssetCommand, _ctx: None = None) -> None:
        async with self.db:
            await self.db.gateway.asset.delete_by_id(cmd.id)
            await self.db.commit()
