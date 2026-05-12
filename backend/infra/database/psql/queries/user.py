from typing import Unpack, final

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker
from sqlalchemy.orm import selectinload

from backend.app.shared.db.query_services.user import UserListFilters, UserWithRoles
from backend.domain.entities.user import User


@final
class ImplUserQueryService:
    def __init__(self, session_maker: async_sessionmaker[AsyncSession]) -> None:
        self._session_maker = session_maker

    async def list_with_roles(
        self, **filters: Unpack[UserListFilters]
    ) -> tuple[list[UserWithRoles], int]:
        offset = filters["offset"]
        limit = filters["limit"]

        stmt = select(User).options(selectinload(User.roles)).offset(offset).limit(limit)
        count_stmt = select(func.count()).select_from(User)

        if (tenant_id := filters.get("tenant_id")) is not None:
            stmt = stmt.where(User.tenant_id == tenant_id)
            count_stmt = count_stmt.where(User.tenant_id == tenant_id)

        if (verified := filters.get("verified")) is not None:
            cond = User.verified_at.is_not(None) if verified else User.verified_at.is_(None)
            stmt = stmt.where(cond)
            count_stmt = count_stmt.where(cond)

        async with self._session_maker() as session:
            items_result = await session.execute(stmt)
            count_result = await session.execute(count_stmt)

        users = items_result.scalars().all()
        total = count_result.scalar_one()
        return [UserWithRoles.from_object(u) for u in users], total
