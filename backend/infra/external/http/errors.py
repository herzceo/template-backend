from __future__ import annotations

from dataclasses import dataclass, field
from http import HTTPStatus
from typing import TYPE_CHECKING

from backend.infra.external.errors import ExternalError
from backend.internal.case import pascal_case_to_snake_case

if TYPE_CHECKING:
    from backend.infra.external.http.sessions.base import HTTPResponse


@dataclass(eq=False)
class HTTPError(ExternalError):
    message: str = "HTTP error"
    code: str = "http_error"
    status: int = 0
    url: str = ""
    body: str = ""
    headers: dict[str, str] = field(default_factory=dict)

    def __init_subclass__(cls, status: HTTPStatus | None = None) -> None:
        super().__init_subclass__()
        if status is not None:
            cls.status = status.value
            cls.message = status.phrase
            cls.code = pascal_case_to_snake_case(cls.__name__.removesuffix("Error"))


class BadRequestError(HTTPError, status=HTTPStatus.BAD_REQUEST): ...


class UnauthorizedError(HTTPError, status=HTTPStatus.UNAUTHORIZED): ...


class ForbiddenError(HTTPError, status=HTTPStatus.FORBIDDEN): ...


class NotFoundError(HTTPError, status=HTTPStatus.NOT_FOUND): ...


class ConflictError(HTTPError, status=HTTPStatus.CONFLICT): ...


class RateLimitedError(HTTPError, status=HTTPStatus.TOO_MANY_REQUESTS): ...


class ServerError(HTTPError, status=HTTPStatus.INTERNAL_SERVER_ERROR): ...


_STATUS_TO_ERROR: dict[int, type[HTTPError]] = {
    sub.status: sub for sub in HTTPError.__subclasses__() if sub.status != 0
}


def http_response_to_error(response: HTTPResponse) -> HTTPError:
    error_cls = _STATUS_TO_ERROR.get(response.status, HTTPError)
    return error_cls(
        message=error_cls.message,
        code=error_cls.code,
        status=response.status,
        url=response.url,
        body=response.text(),
        headers=dict(response.headers),
    )
