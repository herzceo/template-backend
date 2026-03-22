from collections.abc import Callable
from functools import partial
from typing import Any

from litestar import MediaType, Request, Response

from backend.app import errors


def generic_exc_handler_factory(
    status_code: int,
) -> Callable[[Request[Any, Any, Any], errors.ApplicationError], Response[Any]]:
    return partial(error_handler, status_code=status_code)


def error_handler(
    _: Request[Any, Any, Any],
    exc: errors.ApplicationError,
    status_code: int,
) -> Response[Any]:
    return Response(
        {"message": str(exc)},
        status_code=status_code,
        media_type=MediaType.JSON,
    )
