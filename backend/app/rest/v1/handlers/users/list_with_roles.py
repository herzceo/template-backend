from dataclasses import dataclass
from uuid import UUID

from backend.app.rest.v1 import dtos
from backend.app.rest.v1.handlers.base import Command, Handler, HandlerType
from backend.app.shared.db.query_services.gateway import QueryServiceGateway
from backend.app.shared.db.query_services.user import UserWithRoles


class ListUsersWithRolesCommand(Command):
    tenant_id: UUID | None = None
    verified: bool | None = None
    offset: int = 0
    limit: int = 50


@dataclass
class ListUsersWithRolesHandler(
    Handler[ListUsersWithRolesCommand, dtos.PaginatedResponse[UserWithRoles], None],
    type_=HandlerType.READ,
):
    qs: QueryServiceGateway

    async def __call__(
        self, cmd: ListUsersWithRolesCommand, _ctx: None = None
    ) -> dtos.PaginatedResponse[UserWithRoles]:
        items, total = await self.qs.user.list_with_roles(
            tenant_id=cmd.tenant_id,
            verified=cmd.verified,
            offset=cmd.offset,
            limit=cmd.limit,
        )
        return dtos.PaginatedResponse(items=items, total=total, offset=cmd.offset, limit=cmd.limit)
