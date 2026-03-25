from dataclasses import dataclass

from backend.app.errors import AlreadyExistsError
from backend.app.rest.v1 import dtos
from backend.app.rest.v1.handlers.base import Command, Handler, HandlerType
from backend.domain.entities.permission import Permission
from backend.domain.repos.gateway import RepoGateway


class CreatePermissionCommand(Command):
    codename: str
    description: str | None = None


@dataclass
class CreatePermissionHandler(
    Handler[CreatePermissionCommand, dtos.Permission, None], type_=HandlerType.WRITE
):
    gateway: RepoGateway

    async def __call__(self, cmd: CreatePermissionCommand, _ctx: None = None) -> dtos.Permission:
        entity = Permission(
            codename=cmd.codename,
            description=cmd.description,
        )
        created = (await self.gateway.permission.create(entity)).some(AlreadyExistsError())
        await self.gateway.commiter.commit()
        return dtos.Permission.from_object(created)
