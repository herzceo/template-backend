from __future__ import annotations

from dataclasses import dataclass, field
from typing import TYPE_CHECKING, final

from backend.app.shared.ports.events.dbus import PublishOptions

if TYPE_CHECKING:
    from collections.abc import Sequence

    from backend.app.shared.events.base import BaseEvent


_DEFAULT_OPTIONS = PublishOptions()


@final
@dataclass
class MockDBus:
    _published: list[BaseEvent] = field(default_factory=list)

    async def publish(
        self,
        event: BaseEvent,
        /,
        _options: PublishOptions = _DEFAULT_OPTIONS,
    ) -> int:
        self._published.append(event)
        return 0

    async def bulk_publish(
        self,
        events: Sequence[BaseEvent],
        /,
        _options: PublishOptions = _DEFAULT_OPTIONS,
    ) -> list[int]:
        self._published.extend(events)
        return [0] * len(events)

    def get_published(self) -> list[BaseEvent]:
        return list(self._published)

    def get_published_of_type[E: BaseEvent](self, event_type: type[E]) -> list[E]:
        return [e for e in self._published if isinstance(e, event_type)]

    def clear(self) -> None:
        self._published.clear()
