import msgspec.structs
from litestar import Controller, delete, get, patch, post

from backend.app.rest.v1 import dtos
from backend.app.rest.v1.handlers import assets
from backend.internal.di import Depends, inject

from .dtos import UpdateAssetBody


class AssetsController(Controller):
    path = "/assets"
    tags = ("Assets",)

    @get("/")
    @inject
    async def list_assets(
        self,
        handler: Depends[assets.ListAssetsHandler],
        offset: int = 0,
        limit: int = 50,
    ) -> dtos.PaginatedResponse[dtos.Asset]:
        return await handler(assets.ListAssetsCommand(offset=offset, limit=limit))

    @post("/")
    @inject
    async def create_asset(
        self,
        data: assets.CreateAssetCommand,
        handler: Depends[assets.CreateAssetHandler],
    ) -> dtos.Asset:
        return await handler(data)

    @get("/{id:str}")
    @inject
    async def get_asset(
        self,
        id: str,
        handler: Depends[assets.GetAssetHandler],
    ) -> dtos.Asset:
        return await handler(assets.GetAssetCommand(id=id))

    @patch("/{id:str}")
    @inject
    async def update_asset(
        self,
        id: str,
        data: UpdateAssetBody,
        handler: Depends[assets.UpdateAssetHandler],
    ) -> dtos.Asset:
        return await handler(assets.UpdateAssetCommand(id=id, **msgspec.structs.asdict(data)))

    @delete("/{id:str}")
    @inject
    async def delete_asset(
        self,
        id: str,
        handler: Depends[assets.DeleteAssetHandler],
    ) -> None:
        return await handler(assets.DeleteAssetCommand(id=id))
