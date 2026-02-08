from abc import abstractmethod
from collections.abc import AsyncIterable
from typing import Protocol
from uuid import UUID

from backend.domain.entities.base import Base
from backend.internal import Option


class CreateSupported[
    E: Base,
](Protocol):
    @abstractmethod
    async def create(self, entity: E, /) -> Option[E]: ...


class GetByIdSupported[E: Base](Protocol):
    @abstractmethod
    async def get_by_id(self, id_: UUID, /) -> Option[E]: ...


class UpdateSupported[E: Base](Protocol):
    @abstractmethod
    async def update(self, entity: E, /) -> Option[E]: ...


class DeleteByIdSupported[E: Base](Protocol):
    @abstractmethod
    async def delete_by_id(self, id_: UUID, /) -> None: ...


class CountSupported[E: Base](Protocol):
    @abstractmethod
    async def count(self) -> int: ...


class GetForUpdateSupported[E: Base](Protocol):
    @abstractmethod
    async def get_for_update(
        self, id_: UUID, *, nowait: bool = False, skip_locked: bool = False
    ) -> Option[E]: ...


class StreamSupported[E: Base](Protocol):
    @abstractmethod
    async def stream(self) -> AsyncIterable[E]: ...


class CRUDSupported[E: Base](
    CreateSupported[E],
    GetByIdSupported[E],
    UpdateSupported[E],
    DeleteByIdSupported[E],
    CountSupported[E],
    GetForUpdateSupported[E],
    Protocol,
): ...
