from abc import ABC, abstractmethod
from typing import ClassVar, get_args

from backend.internal.dto import StructDTO


class Context(StructDTO): ...


class Command(StructDTO): ...


class Handler[C: Command, R: StructDTO | None](ABC):
    command_cls: ClassVar[type[Command]]

    def __init_subclass__(cls, /) -> None:
        cls.command_cls = get_args(cls.__orig_bases__[-1])[0]  # type: ignore[attr-defined]

    @abstractmethod
    async def __call__(self, cmd: C, ctx: Context) -> R:
        raise NotImplementedError
