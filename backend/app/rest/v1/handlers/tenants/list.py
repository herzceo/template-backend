from dataclasses import dataclass

from backend.app.rest.v1 import dtos
from backend.app.rest.v1.handlers.base import Command, Handler, HandlerType
from backend.domain.repos.gateway import RepoGateway


class ListTenantsCommand(Command):
    offset: int = 0
    limit: int = 50


@dataclass
class ListTenantsHandler(
    Handler[ListTenantsCommand, dtos.PaginatedResponse[dtos.Tenant], None],
    type_=HandlerType.READ,
):
    gateway: RepoGateway

    async def __call__(
        self, cmd: ListTenantsCommand, _ctx: None = None
    ) -> dtos.PaginatedResponse[dtos.Tenant]:
        items = await self.gateway.tenant.list_with_offset(offset=cmd.offset, limit=cmd.limit)
        total = await self.gateway.tenant.count()
        return dtos.PaginatedResponse(
            items=[dtos.Tenant.from_object(i) for i in items],
            total=total,
            offset=cmd.offset,
            limit=cmd.limit,
        )
