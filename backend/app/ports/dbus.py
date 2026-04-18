from __future__ import annotations

from abc import abstractmethod
from typing import TYPE_CHECKING, Protocol

from msgspec import Struct

if TYPE_CHECKING:
    from collections.abc import Sequence
    from datetime import datetime

    from backend.app.shared.events import BaseEvent


class PublishOptions(Struct):
    priority: int = 0
    execution_lock: str | None = None
    queueing_lock: str | None = None
    scheduled_at: datetime | None = None


class DBus(Protocol):
    @abstractmethod
    async def publish(
        self,
        event: BaseEvent,
        /,
        options: PublishOptions = ...,
    ) -> int: ...

    @abstractmethod
    async def bulk_publish(
        self,
        events: Sequence[BaseEvent],
        /,
        options: PublishOptions = ...,
    ) -> list[int]: ...
