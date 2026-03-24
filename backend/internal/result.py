from __future__ import annotations

from dataclasses import dataclass
from typing import NoReturn, Protocol


class ToException(Protocol):
    def to_exception(self) -> Exception: ...


@dataclass(slots=True, frozen=True)
class Ok[T]:
    value: T

    def raise_(self) -> T:
        return self.value


@dataclass(slots=True, frozen=True)
class Err[E: Exception | ToException]:
    error: E

    def raise_(self) -> NoReturn:
        if isinstance(self.error, Exception):
            raise self.error
        raise self.error.to_exception()


type Result[T, E: Exception | ToException] = Ok[T] | Err[E]
