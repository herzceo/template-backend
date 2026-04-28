from dataclasses import dataclass
from uuid import UUID

from backend.app.rest.v1.dtos.presign import PresignedUploadResponse
from backend.app.rest.v1.handlers.base import Command, Handler, HandlerType
from backend.app.shared.ports.storage import ObjectStore


class PresignAssetCommand(Command):
    user_id: UUID
    original_filename: str


@dataclass
class PresignAssetHandler(
    Handler[PresignAssetCommand, PresignedUploadResponse, None],
    type_=HandlerType.READ,
):
    store: ObjectStore

    async def __call__(
        self, cmd: PresignAssetCommand, _ctx: None = None
    ) -> PresignedUploadResponse:
        result = await self.store.request_upload(
            user_id=cmd.user_id,
            original_filename=cmd.original_filename,
        )
        return PresignedUploadResponse(
            url=result.url,
            key=result.key,
            expires_in=result.expires_in,
        )
