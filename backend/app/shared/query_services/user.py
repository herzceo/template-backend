from abc import abstractmethod
from datetime import datetime
from typing import NotRequired, Protocol, TypedDict, Unpack
from uuid import UUID

from backend.app.rest.v1.dtos.roles import Role
from backend.internal.dto import StructDTO


class UserWithRoles(StructDTO):
    id: UUID
    username: str
    email: str | None
    first_name: str
    last_name: str
    avatar_url: str | None
    active: bool
    tenant_id: UUID
    created_at: datetime
    updated_at: datetime
    roles: list[Role]


class UserListFilters(TypedDict):
    tenant_id: NotRequired[UUID | None]
    verified: NotRequired[bool | None]
    offset: int
    limit: int


class UserQueryService(Protocol):
    @abstractmethod
    async def list_with_roles(
        self, **filters: Unpack[UserListFilters]
    ) -> tuple[list[UserWithRoles], int]: ...
