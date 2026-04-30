from collections.abc import AsyncIterable
from typing import ClassVar, TypeVar, get_args, get_origin
from uuid import UUID

from sqlalchemy import delete, func, insert, select, update
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession

from backend.domain.entities.base import Base
from backend.domain.repos.base import CountSupported as ICountSupported
from backend.domain.repos.base import CreateSupported as ICreateSupported
from backend.domain.repos.base import DeleteByIdSupported as IDeleteByIdSupported
from backend.domain.repos.base import GetByIdSupported as IGetByIdSupported
from backend.domain.repos.base import GetForUpdateSupported as IGetForUpdateSupported
from backend.domain.repos.base import OffsetPaginationSupported as IOffsetPaginationSupported
from backend.domain.repos.base import StreamSupported as IStreamSupported
from backend.domain.repos.base import UpdateSupported as IUpdateSupported
from backend.internal import Option


class BaseRepo[E: Base]:
    __slots__ = ("_session",)

    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    _entity: ClassVar[type[E]]

    def __init_subclass__(cls) -> None:
        for base in cls.__orig_bases__:  # type: ignore[attr-defined]
            if issubclass(get_origin(base) or base, BaseRepo):
                _entity = get_args(base)[0]
                if type(_entity) is TypeVar:
                    continue
                cls._entity = _entity
                return


class ImplCreateSupported[E: Base](ICreateSupported[E], BaseRepo[E]):
    __slots__ = ()

    async def create(self, entity: E, /) -> Option[E]:
        stmt = insert(self._entity).values(**entity.to_builtins()).returning(self._entity)
        try:
            result = await self._session.execute(stmt)
        except IntegrityError:
            return Option(None)
        return Option(result.scalar_one_or_none())


class ImplBulkCreateSupported[E: Base](BaseRepo[E]):
    __slots__ = ()

    async def bulk_create(self, entities: list[E], /) -> list[E]:
        if not entities:
            return []
        stmt = (
            insert(self._entity).values([e.to_builtins() for e in entities]).returning(self._entity)
        )
        result = await self._session.execute(stmt)
        return list(result.scalars().all())


class ImplGetByIdSupported[E: Base](IGetByIdSupported[E], BaseRepo[E]):
    __slots__ = ()

    async def get_by_id(self, id_: UUID, /) -> Option[E]:
        result = await self._session.get(self._entity, id_)
        return Option(result)


class ImplUpdateSupported[E: Base](IUpdateSupported[E], BaseRepo[E]):
    __slots__ = ()

    async def update(self, entity: E, /) -> Option[E]:
        stmt = (
            update(self._entity)
            .values(**entity.to_builtins())
            .where(self._entity.id == entity.id)
            .returning(self._entity)
        )
        result = await self._session.execute(stmt)
        return Option(result.scalar_one_or_none())


class ImplDeleteByIdSupported[E: Base](IDeleteByIdSupported[E], BaseRepo[E]):
    __slots__ = ()

    async def delete_by_id(self, id_: UUID, /) -> None:
        stmt = delete(self._entity).where(self._entity.id == id_)
        await self._session.execute(stmt)


class ImplCountSupported[E: Base](ICountSupported[E], BaseRepo[E]):
    __slots__ = ()

    async def count(self) -> int:
        stmt = select(func.count()).select_from(self._entity)
        result = await self._session.execute(stmt)
        return result.scalar_one()


class ImplGetForUpdateSupported[E: Base](IGetForUpdateSupported[E], BaseRepo[E]):
    __slots__ = ()

    async def get_for_update(
        self, id_: UUID, *, nowait: bool = False, skip_locked: bool = False
    ) -> Option[E]:
        stmt = (
            select(self._entity)
            .where(self._entity.id == id_)
            .with_for_update(nowait=nowait, skip_locked=skip_locked)
        )
        result = await self._session.execute(stmt)
        return Option(result.scalar_one_or_none())


class ImplStreamSupported[E: Base](IStreamSupported[E], BaseRepo[E]):
    __slots__ = ()

    async def stream(self) -> AsyncIterable[E]:
        stmt = select(self._entity).order_by(self._entity.id)
        return await self._session.stream_scalars(stmt)


class ImplOffsetPaginationSupported[E: Base](IOffsetPaginationSupported[E], BaseRepo[E]):
    __slots__ = ()

    async def list_with_offset(self, *, offset: int = 0, limit: int = 50) -> list[E]:
        stmt = select(self._entity).offset(offset).limit(limit).order_by(self._entity.id)
        result = await self._session.execute(stmt)
        return list(result.scalars().all())


class ImplCRUDSupported[E: Base](
    ImplCreateSupported[E],
    ImplGetByIdSupported[E],
    ImplUpdateSupported[E],
    ImplDeleteByIdSupported[E],
    ImplCountSupported[E],
    ImplGetForUpdateSupported[E],
    ImplOffsetPaginationSupported[E],
    BaseRepo[E],
):
    __slots__ = ()

    def __init__(self, session: AsyncSession) -> None:
        self._session = session
