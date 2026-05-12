from dataclasses import dataclass
from uuid import UUID

from backend.app.errors import AlreadyExistsError, NotFoundError
from backend.app.rest.v1 import dtos
from backend.app.rest.v1.handlers.base import Command, Handler, HandlerType
from backend.app.shared.db.database import Database
from backend.app.shared.ports.storage import ObjectStore
from backend.domain.entities.asset import Asset
from backend.domain.enums import AssetContentType


class CreateAssetCommand(Command):
    temp_key: str
    content_type: AssetContentType
    original_filename: str
    user_id: UUID


@dataclass
class CreateAssetHandler(
    Handler[CreateAssetCommand, dtos.Asset, None],
    type_=HandlerType.WRITE,
):
    db: Database
    store: ObjectStore

    async def __call__(self, cmd: CreateAssetCommand, _ctx: None = None) -> dtos.Asset:
        async with self.db:
            user = (await self.db.gateway.user.get_by_id(cmd.user_id)).some(
                NotFoundError(message="User not found")
            )
            tenant_id = user.tenant_id

        confirmed = await self.store.confirm_upload(
            pending_key=cmd.temp_key,
            user_id=cmd.user_id,
            tenant_id=tenant_id,
            original_filename=cmd.original_filename,
        )

        async with self.db:
            entity = Asset(
                key=confirmed.key,
                content_type=cmd.content_type,
                size_bytes=confirmed.size,
                tenant_id=tenant_id,
                uploader_id=cmd.user_id,
                original_filename=cmd.original_filename,
                blurhash=confirmed.blurhash,
            )
            created = (await self.db.gateway.asset.create(entity)).some(AlreadyExistsError())
            await self.db.commit()

        return dtos.Asset.from_object(created)
