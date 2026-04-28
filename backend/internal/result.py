from __future__ import annotations

from typing import NoReturn, Protocol, runtime_checkable

from backend.internal.dto import StructDTO


@runtime_checkable
class ToException(Protocol):
    def to_exception(self) -> Exception: ...


class Ok[T](StructDTO, tag="ok"):
    data: T

    def raise_(self) -> T:
        return self.data


class Err[E](StructDTO, tag="error"):
    error: E

    def raise_(self) -> NoReturn:
        if isinstance(self.error, Exception):
            raise self.error
        if isinstance(self.error, ToException):
            raise self.error.to_exception()
        msg = f"Cannot raise error of type {type(self.error).__name__}"
        raise TypeError(msg)


type Result[T, E] = Ok[T] | Err[E]
