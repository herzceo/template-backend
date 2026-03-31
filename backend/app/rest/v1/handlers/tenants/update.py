from dataclasses import dataclass
from typing import Any

from uuid_utils.compat import UUID

from backend.app.errors import NotFoundError
from backend.app.rest.v1 import dtos
from backend.app.rest.v1.handlers.base import Command, Handler, HandlerType
from backend.domain.repos.database import Database


class UpdateTenantCommand(Command):
    id: str
    name: str | None = None
    slug: str | None = None
    settings: dict[str, Any] | None = None
    owner_id: str | None = None


@dataclass
class UpdateTenantHandler(Handler[UpdateTenantCommand, dtos.Tenant, None], type_=HandlerType.WRITE):
    db: Database

    async def __call__(self, cmd: UpdateTenantCommand, _ctx: None = None) -> dtos.Tenant:
        async with self.db:
            entity = (await self.db.gateway.tenant.get_by_id(UUID(cmd.id))).some(NotFoundError())
            if cmd.name is not None:
                entity.name = cmd.name
            if cmd.slug is not None:
                entity.slug = cmd.slug
            if cmd.settings is not None:
                entity.settings = cmd.settings
            if cmd.owner_id is not None:
                entity.owner_id = UUID(cmd.owner_id)
            updated = (await self.db.gateway.tenant.update(entity)).some(NotFoundError())
            await self.db.commit()
        return dtos.Tenant.from_object(updated)
