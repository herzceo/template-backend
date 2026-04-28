from collections.abc import Callable
from functools import partial
from typing import Any

from litestar import MediaType, Request, Response
from litestar.exceptions import HTTPException

from backend.app import errors
from backend.entry.rest.common.response import ErrorDetail
from backend.internal.result import Err

HTTP_CODE_TO_ERROR_CODE: dict[int, str] = {
    400: "bad_request",
    401: "unauthorized",
    403: "forbidden",
    404: "not_found",
    405: "method_not_allowed",
    409: "conflict",
    422: "validation_error",
    429: "too_many_requests",
    500: "internal_error",
}


def _err_response(error: ErrorDetail, status_code: int) -> Response[Any]:
    return Response(
        Err(error=error).to_builtins(),
        status_code=status_code,
        media_type=MediaType.JSON,
    )


def generic_exc_handler_factory(
    status_code: int,
) -> Callable[[Request[Any, Any, Any], errors.ApplicationError], Response[Any]]:
    return partial(error_handler, status_code=status_code)


def error_handler(
    _: Request[Any, Any, Any],
    exc: errors.ApplicationError,
    status_code: int,
) -> Response[Any]:
    if isinstance(exc, errors.DetailedError):
        detail = ErrorDetail(code=exc.code, message=exc.message, details=exc.details)
    else:
        detail = ErrorDetail(code="application_error", message=str(exc))

    return _err_response(detail, status_code)


def http_exc_handler(
    _: Request[Any, Any, Any],
    exc: HTTPException,
) -> Response[Any]:
    code = HTTP_CODE_TO_ERROR_CODE.get(exc.status_code, f"http_{exc.status_code}")
    extra = exc.extra if isinstance(exc.extra, dict) else {}
    detail = ErrorDetail(code=code, message=exc.detail, details=extra)
    return _err_response(detail, exc.status_code)


def fallback_exc_handler(
    _: Request[Any, Any, Any],
    _exc: Exception,
) -> Response[Any]:
    detail = ErrorDetail(code="internal_error", message="Internal server error")
    return _err_response(detail, 500)
