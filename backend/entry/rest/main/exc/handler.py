import logging
import traceback
from collections.abc import Callable
from functools import partial
from typing import Any

from litestar import MediaType, Request, Response
from litestar.exceptions import HTTPException

from backend.app import errors
from backend.entry.rest.common.response import ErrorDetail
from backend.internal.result import Err

_log = logging.getLogger(__name__)

HTTP_CODE_TO_GRPC_STATUS: dict[int, str] = {
    400: "INVALID_ARGUMENT",
    401: "UNAUTHENTICATED",
    403: "PERMISSION_DENIED",
    404: "NOT_FOUND",
    405: "UNIMPLEMENTED",
    409: "ALREADY_EXISTS",
    422: "INVALID_ARGUMENT",
    429: "RESOURCE_EXHAUSTED",
    500: "INTERNAL",
}

ERROR_CODE_TO_GRPC_STATUS: dict[str, str] = {
    "not_found": "NOT_FOUND",
    "invalid_input": "INVALID_ARGUMENT",
    "validation_failed": "INVALID_ARGUMENT",
    "already_exists": "ALREADY_EXISTS",
    "conflict": "ABORTED",
    "permission_denied": "PERMISSION_DENIED",
    "authentication_required": "UNAUTHENTICATED",
    "internal_error": "INTERNAL",
    "application_error": "INTERNAL",
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
        grpc_status = ERROR_CODE_TO_GRPC_STATUS.get(exc.code, "INTERNAL")
        details: list[dict[str, Any]] = [
            {
                "@type": "type.googleapis.com/google.rpc.ErrorInfo",
                "reason": exc.code.upper(),
                "domain": "api",
                "metadata": exc.details,
            }
        ]
        detail = ErrorDetail(
            code=status_code,
            message=exc.message,
            status=grpc_status,
            details=details,
        )
    else:
        detail = ErrorDetail(
            code=status_code,
            message=str(exc),
            status="INTERNAL",
        )
    return _err_response(detail, status_code)


def http_exc_handler(
    _: Request[Any, Any, Any],
    exc: HTTPException,
) -> Response[Any]:
    grpc_status = HTTP_CODE_TO_GRPC_STATUS.get(exc.status_code, "INTERNAL")
    extra = exc.extra if isinstance(exc.extra, dict) else {}
    detail = ErrorDetail(
        code=exc.status_code,
        message=exc.detail,
        status=grpc_status,
        details=[{"@type": "type.googleapis.com/google.rpc.ErrorInfo", "metadata": extra}]
        if extra
        else [],
    )
    return _err_response(detail, exc.status_code)


def fallback_exc_handler(
    _: Request[Any, Any, Any],
    _exc: Exception,
) -> Response[Any]:
    _log.error(
        "Unhandled exception: %s\n%s",
        _exc,
        "".join(traceback.format_exception(type(_exc), _exc, _exc.__traceback__)),
    )
    detail = ErrorDetail(code=500, message="Internal server error", status="INTERNAL")
    return _err_response(detail, 500)
