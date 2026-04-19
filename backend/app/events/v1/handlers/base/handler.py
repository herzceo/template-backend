from abc import ABC, abstractmethod
from typing import Any, ClassVar, get_args

from backend.app.shared.events.base import BaseEvent
from backend.app.shared.handlers.types import HandlerType

_DEFINED_EVENT_HANDLERS: dict[str, type["EventHandler[Any]"]] = {}


class EventHandler[E: BaseEvent](ABC):
    event_type: ClassVar[type[BaseEvent]]
    type_: ClassVar[HandlerType]

    def __init_subclass__(cls, /, type_: HandlerType = HandlerType.WRITE) -> None:
        cls.event_type = get_args(cls.__orig_bases__[-1])[0]  # type: ignore[attr-defined]
        cls.type_ = type_
        if not getattr(cls, "__abstractmethods__", None):
            _DEFINED_EVENT_HANDLERS[cls.event_type.name] = cls

    @abstractmethod
    async def __call__(self, event: E, /) -> None:
        raise NotImplementedError


def get_defined_event_handlers() -> dict[str, type["EventHandler[Any]"]]:
    return _DEFINED_EVENT_HANDLERS
