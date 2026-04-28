from collections.abc import Callable, Coroutine
from functools import wraps
from typing import Any

from msgspec import field

from backend.internal.dto import StructDTO
from backend.internal.result import Ok, Result


class ErrorDetail(StructDTO):
    code: str
    message: str
    details: dict[str, Any] = field(default_factory=dict)


type ResultResponse[T] = Result[T, ErrorDetail]


def result[**P, T](
    fn: Callable[P, Coroutine[Any, Any, T]],
) -> Callable[P, Coroutine[Any, Any, ResultResponse[T]]]:
    @wraps(fn)
    async def wrapper(*args: P.args, **kwargs: P.kwargs) -> ResultResponse[T]:
        res = await fn(*args, **kwargs)
        return Ok(data=res)

    return wrapper
