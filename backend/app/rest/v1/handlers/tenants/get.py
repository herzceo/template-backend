from dataclasses import dataclass

from uuid_utils.compat import UUID

from backend.app.errors import NotFoundError
from backend.app.rest.v1 import dtos
from backend.app.rest.v1.handlers.base import Command, Handler, HandlerType
from backend.domain.repos.gateway import RepoGateway


class GetTenantCommand(Command):
    id: str


@dataclass
class GetTenantHandler(Handler[GetTenantCommand, dtos.Tenant, None], type_=HandlerType.READ):
    gateway: RepoGateway

    async def __call__(self, cmd: GetTenantCommand, _ctx: None = None) -> dtos.Tenant:
        tenant = (await self.gateway.tenant.get_by_id(UUID(cmd.id))).some(NotFoundError())
        return dtos.Tenant.from_object(tenant)
