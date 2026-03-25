from typing import final
from uuid import UUID

from sqlalchemy import select
from sqlalchemy.orm import selectinload

from backend.domain.entities.role import Role
from backend.domain.entities.user import User
from backend.domain.repos.user import UserRepo
from backend.internal import Option

from .base import ImplCRUDSupported


@final
class ImplUserRepo(ImplCRUDSupported[User], UserRepo):
    __slots__ = ()

    async def get_by_login(self, login: str) -> Option[User]:
        stmt = select(User).where(User.login == login)
        result = await self._session.execute(stmt)
        return Option(result.scalar_one_or_none())

    async def get_by_email(self, email: str) -> Option[User]:
        stmt = select(User).where(User.email == email)
        result = await self._session.execute(stmt)
        return Option(result.scalar_one_or_none())

    async def assign_role(self, user_id: UUID, role_id: UUID) -> None:
        stmt = select(User).where(User.id == user_id).options(selectinload(User.roles))
        result = await self._session.execute(stmt)
        user = result.scalar_one()
        role = await self._session.get_one(Role, role_id)
        user.roles.append(role)

    async def revoke_role(self, user_id: UUID, role_id: UUID) -> None:
        stmt = select(User).where(User.id == user_id).options(selectinload(User.roles))
        result = await self._session.execute(stmt)
        user = result.scalar_one()
        role = await self._session.get_one(Role, role_id)
        user.roles.remove(role)

    async def get_roles(self, user_id: UUID) -> list[Role]:
        stmt = select(User).where(User.id == user_id).options(selectinload(User.roles))
        result = await self._session.execute(stmt)
        user = result.scalar_one()
        return list(user.roles)
