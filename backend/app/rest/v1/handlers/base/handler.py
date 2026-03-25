from abc import ABC, abstractmethod
from typing import Any, ClassVar, get_args

from backend.internal.dto import StructDTO

from .type import HandlerType


class Command(StructDTO): ...


_DEFINED_HANDLERS: dict[type[Command], type["Handler[Any, Any, Any]"]] = {}


class Handler[C: Command, R: StructDTO | None, X: StructDTO | None](ABC):
    command_dto: ClassVar[type[Command]]
    type_: ClassVar[HandlerType]

    def __init_subclass__(cls, /, type_: HandlerType = HandlerType.WRITE) -> None:
        cls.command_dto = get_args(cls.__orig_bases__[-1])[0]  # type: ignore[attr-defined]
        cls.type_ = type_
        if not getattr(cls, "__abstractmethods__", None):
            _DEFINED_HANDLERS[cls.command_dto] = cls

    @abstractmethod
    async def __call__(self, __cmd: C, ctx: X, /) -> R:
        raise NotImplementedError


def get_defined_handlers() -> dict[type[Command], type["Handler[Any, Any, Any]"]]:
    return _DEFINED_HANDLERS
