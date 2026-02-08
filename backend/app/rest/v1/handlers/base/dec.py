from dataclasses import dataclass
from typing import Any, dataclass_transform

from .base import Command, Handler

_COMMAND_TO_HANDLER: dict[type[Command], type[Handler[Any, Any]]] = {}


@dataclass_transform()
def handler[T: Handler[Any, Any]](cls: type[T]) -> type[T]:
    cls = dataclass(slots=True, frozen=True, eq=False, match_args=False)(cls)
    _COMMAND_TO_HANDLER[cls.command_cls] = cls
    return cls


def get_defined_handlers() -> dict[type[Command], type[Handler[Any, Any]]]:
    return _COMMAND_TO_HANDLER
