from dataclasses import dataclass
from uuid import UUID

from backend.app.errors import NotFoundError
from backend.app.rest.v1 import dtos
from backend.app.rest.v1.handlers.base import Command, Handler, HandlerType
from backend.app.shared.db.database import Database


class GetAssetCommand(Command):
    id: UUID


@dataclass
class GetAssetHandler(Handler[GetAssetCommand, dtos.Asset, None], type_=HandlerType.READ):
    db: Database

    async def __call__(self, cmd: GetAssetCommand, _ctx: None = None) -> dtos.Asset:
        async with self.db:
            asset = (await self.db.gateway.asset.get_by_id(cmd.id)).some(NotFoundError())
        return dtos.Asset.from_object(asset)
