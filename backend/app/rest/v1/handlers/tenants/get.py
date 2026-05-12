from dataclasses import dataclass
from uuid import UUID

from backend.app.errors import NotFoundError
from backend.app.rest.v1 import dtos
from backend.app.rest.v1.handlers.base import Command, Handler, HandlerType
from backend.app.shared.db.database import Database


class GetTenantCommand(Command):
    id: UUID


@dataclass
class GetTenantHandler(Handler[GetTenantCommand, dtos.Tenant, None], type_=HandlerType.READ):
    db: Database

    async def __call__(self, cmd: GetTenantCommand, _ctx: None = None) -> dtos.Tenant:
        async with self.db:
            tenant = (await self.db.gateway.tenant.get_by_id(cmd.id)).some(NotFoundError())
        return dtos.Tenant.from_object(tenant)
