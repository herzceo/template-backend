from dataclasses import dataclass
from uuid import UUID

from backend.app.errors import NotFoundError
from backend.app.rest.v1 import dtos
from backend.app.rest.v1.handlers.base import Command, Handler, HandlerType
from backend.app.shared.db.database import Database


class UpdateAssetCommand(Command):
    id: UUID
    blurhash: str | None = None
    original_filename: str | None = None


@dataclass
class UpdateAssetHandler(Handler[UpdateAssetCommand, dtos.Asset, None], type_=HandlerType.WRITE):
    db: Database

    async def __call__(self, cmd: UpdateAssetCommand, _ctx: None = None) -> dtos.Asset:
        async with self.db:
            entity = (await self.db.gateway.asset.get_by_id(cmd.id)).some(NotFoundError())
            if cmd.blurhash is not None:
                entity.blurhash = cmd.blurhash
            if cmd.original_filename is not None:
                entity.original_filename = cmd.original_filename
            updated = (await self.db.gateway.asset.update(entity)).some(NotFoundError())
            await self.db.commit()
        return dtos.Asset.from_object(updated)
