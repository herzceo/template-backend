from dataclasses import dataclass

from backend.app.rest.v1 import dtos
from backend.app.rest.v1.handlers.base import Command, Handler, HandlerType
from backend.domain.repos.gateway import RepoGateway


class ListAssetsCommand(Command):
    offset: int = 0
    limit: int = 50


@dataclass
class ListAssetsHandler(
    Handler[ListAssetsCommand, dtos.PaginatedResponse[dtos.Asset], None],
    type_=HandlerType.READ,
):
    gateway: RepoGateway

    async def __call__(
        self, cmd: ListAssetsCommand, _ctx: None = None
    ) -> dtos.PaginatedResponse[dtos.Asset]:
        items = await self.gateway.asset.list_with_offset(offset=cmd.offset, limit=cmd.limit)
        total = await self.gateway.asset.count()
        return dtos.PaginatedResponse(
            items=[dtos.Asset.from_object(i) for i in items],
            total=total,
            offset=cmd.offset,
            limit=cmd.limit,
        )
