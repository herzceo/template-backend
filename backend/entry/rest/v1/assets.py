from typing import Any
from uuid import UUID

import msgspec.structs
from litestar import Controller, Request, delete, get, patch, post

from backend.app.rest.v1 import dtos
from backend.app.rest.v1.handlers import assets
from backend.entry.rest.common.response import result
from backend.internal.di import Depends, inject

from .dtos import ConfirmAssetUploadBody, PresignAssetBody, UpdateAssetBody


class AssetsController(Controller):
    path = "/assets"
    tags = ("Assets",)

    @post("/presign")
    @inject
    @result
    async def presign_asset(
        self,
        data: PresignAssetBody,
        handler: Depends[assets.PresignAssetHandler],
        request: Request[Any, Any, Any],
    ) -> dtos.PresignedUploadResponse:
        return await handler(
            assets.PresignAssetCommand(
                user_id=request.auth.user_id,
                original_filename=data.original_filename,
            )
        )

    @post("/")
    @inject
    @result
    async def create_asset(
        self,
        data: ConfirmAssetUploadBody,
        handler: Depends[assets.CreateAssetHandler],
        request: Request[Any, Any, Any],
    ) -> dtos.Asset:
        return await handler(
            assets.CreateAssetCommand(
                temp_key=data.temp_key,
                content_type=data.content_type,
                original_filename=data.original_filename,
                user_id=request.auth.user_id,
            )
        )

    @get("/")
    @inject
    @result
    async def list_assets(
        self,
        handler: Depends[assets.ListAssetsHandler],
        offset: int = 0,
        limit: int = 50,
    ) -> dtos.PaginatedResponse[dtos.Asset]:
        return await handler(assets.ListAssetsCommand(offset=offset, limit=limit))

    @get("/{id:str}")
    @inject
    @result
    async def get_asset(
        self,
        id: str,
        handler: Depends[assets.GetAssetHandler],
    ) -> dtos.Asset:
        return await handler(assets.GetAssetCommand(id=UUID(id)))

    @patch("/{id:str}")
    @inject
    @result
    async def update_asset(
        self,
        id: str,
        data: UpdateAssetBody,
        handler: Depends[assets.UpdateAssetHandler],
    ) -> dtos.Asset:
        return await handler(assets.UpdateAssetCommand(id=UUID(id), **msgspec.structs.asdict(data)))

    @delete("/{id:str}")
    @inject
    async def delete_asset(
        self,
        id: str,
        handler: Depends[assets.DeleteAssetHandler],
    ) -> None:
        return await handler(assets.DeleteAssetCommand(id=UUID(id)))
