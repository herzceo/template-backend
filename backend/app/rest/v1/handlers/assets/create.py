from dataclasses import dataclass
from uuid import UUID

from backend.app.errors import AlreadyExistsError
from backend.app.rest.v1 import dtos
from backend.app.rest.v1.handlers.base import Command, Handler, HandlerType
from backend.domain.entities.asset import Asset
from backend.domain.repos.database import Database


class CreateAssetCommand(Command):
    key: str
    content_type: str
    size_bytes: int
    tenant_id: UUID
    uploader_id: UUID
    blurhash: str | None = None
    original_filename: str | None = None


@dataclass
class CreateAssetHandler(Handler[CreateAssetCommand, dtos.Asset, None], type_=HandlerType.WRITE):
    db: Database

    async def __call__(self, cmd: CreateAssetCommand, _ctx: None = None) -> dtos.Asset:
        async with self.db:
            entity = Asset(
                key=cmd.key,
                content_type=cmd.content_type,
                size_bytes=cmd.size_bytes,
                tenant_id=cmd.tenant_id,
                uploader_id=cmd.uploader_id,
                blurhash=cmd.blurhash,
                original_filename=cmd.original_filename,
            )
            created = (await self.db.gateway.asset.create(entity)).some(AlreadyExistsError())
            await self.db.commit()
        return dtos.Asset.from_object(created)
