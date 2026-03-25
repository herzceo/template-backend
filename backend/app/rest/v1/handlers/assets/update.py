from dataclasses import dataclass

from uuid_utils.compat import UUID

from backend.app.errors import NotFoundError
from backend.app.rest.v1 import dtos
from backend.app.rest.v1.handlers.base import Command, Handler, HandlerType
from backend.domain.repos.gateway import RepoGateway


class UpdateAssetCommand(Command):
    id: str
    blurhash: str | None = None
    original_filename: str | None = None


@dataclass
class UpdateAssetHandler(Handler[UpdateAssetCommand, dtos.Asset, None], type_=HandlerType.WRITE):
    gateway: RepoGateway

    async def __call__(self, cmd: UpdateAssetCommand, _ctx: None = None) -> dtos.Asset:
        entity = (await self.gateway.asset.get_by_id(UUID(cmd.id))).some(NotFoundError())
        if cmd.blurhash is not None:
            entity.blurhash = cmd.blurhash
        if cmd.original_filename is not None:
            entity.original_filename = cmd.original_filename
        updated = (await self.gateway.asset.update(entity)).some(NotFoundError())
        await self.gateway.commiter.commit()
        return dtos.Asset.from_object(updated)
