from dataclasses import dataclass
from typing import Any

from uuid_utils.compat import UUID

from backend.app.errors import AlreadyExistsError
from backend.app.rest.v1 import dtos
from backend.app.rest.v1.handlers.base import Command, Handler, HandlerType
from backend.domain.entities.tenant import Tenant
from backend.domain.repos.gateway import RepoGateway


class CreateTenantCommand(Command):
    name: str
    slug: str
    settings: dict[str, Any] | None = None
    owner_id: str | None = None


@dataclass
class CreateTenantHandler(Handler[CreateTenantCommand, dtos.Tenant, None], type_=HandlerType.WRITE):
    gateway: RepoGateway

    async def __call__(self, cmd: CreateTenantCommand, _ctx: None = None) -> dtos.Tenant:
        entity = Tenant(
            name=cmd.name,
            slug=cmd.slug,
            settings=cmd.settings,
            owner_id=UUID(cmd.owner_id) if cmd.owner_id else None,
        )
        created = (await self.gateway.tenant.create(entity)).some(AlreadyExistsError())
        await self.gateway.commiter.commit()
        return dtos.Tenant.from_object(created)
