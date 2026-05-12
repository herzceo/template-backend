from dataclasses import dataclass
from typing import Any
from uuid import UUID

from backend.app.errors import AlreadyExistsError
from backend.app.rest.v1 import dtos
from backend.app.rest.v1.handlers.base import Command, Handler, HandlerType
from backend.app.shared.db.database import Database
from backend.domain.entities.tenant import Tenant


class CreateTenantCommand(Command):
    name: str
    slug: str
    settings: dict[str, Any] | None = None
    owner_id: UUID | None = None


@dataclass
class CreateTenantHandler(Handler[CreateTenantCommand, dtos.Tenant, None], type_=HandlerType.WRITE):
    db: Database

    async def __call__(self, cmd: CreateTenantCommand, _ctx: None = None) -> dtos.Tenant:
        async with self.db:
            entity = Tenant(
                name=cmd.name,
                slug=cmd.slug,
                settings=cmd.settings,
                owner_id=cmd.owner_id,
            )
            created = (await self.db.gateway.tenant.create(entity)).some(AlreadyExistsError())
            await self.db.commit()
        return dtos.Tenant.from_object(created)
