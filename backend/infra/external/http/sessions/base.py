from __future__ import annotations

from collections.abc import Callable, Sequence
from dataclasses import dataclass, field
from http import HTTPStatus
from typing import TYPE_CHECKING, Any, Protocol, Required, Self, TypedDict, Unpack

import msgspec

from backend.infra.external.errors import DecodeError
from backend.infra.external.http.errors import HTTPError, http_response_to_error
from backend.internal.dto import StructDTO
from backend.internal.result import Err, Ok, Result

if TYPE_CHECKING:
    from collections.abc import Mapping


@dataclass(slots=True)
class Request:
    method: str
    url: str
    headers: dict[str, str] = field(default_factory=dict)
    params: dict[str, str] = field(default_factory=dict)
    json: Any = None
    data: bytes | None = None
    timeout: float | None = None


class RequestOpts(TypedDict, total=False):
    url: Required[str]
    headers: dict[str, str]
    params: dict[str, str]
    json: Any
    data: bytes
    timeout: float
    middlewares: Sequence[Middleware]


class Handler(Protocol):
    async def __call__(self, request: Request) -> HTTPResponse: ...


type Middleware = Callable[[Handler], Handler]


class HTTPResponse:
    __slots__ = ("_body", "_headers", "_status", "_url")

    def __init__(
        self,
        status: int,
        url: str,
        headers: Mapping[str, str],
        body: bytes,
    ) -> None:
        self._status = status
        self._url = url
        self._headers = headers
        self._body = body

    @property
    def status(self) -> int:
        return self._status

    @property
    def url(self) -> str:
        return self._url

    @property
    def headers(self) -> Mapping[str, str]:
        return self._headers

    @property
    def is_success(self) -> bool:
        return HTTPStatus.OK <= self._status < HTTPStatus.BAD_REQUEST

    def json(self) -> Any:
        return msgspec.json.decode(self._body)

    def text(self, encoding: str = "utf-8") -> str:
        return self._body.decode(encoding)

    def read(self) -> bytes:
        return self._body

    def as_result[T: StructDTO](self, response_type: type[T]) -> Result[T, HTTPResponse]:
        if not self.is_success:
            return Err(self)
        try:
            decoded = msgspec.json.decode(self._body, type=response_type)
        except (msgspec.DecodeError, msgspec.ValidationError):
            return Err(self)
        return Ok(decoded)

    def decode[T: StructDTO](self, response_type: type[T]) -> T:
        try:
            return msgspec.json.decode(self._body, type=response_type)
        except (msgspec.DecodeError, msgspec.ValidationError) as e:
            raise DecodeError(
                message=f"Failed to decode response from {self._url}: {e}",
                raw=self._body,
            ) from e

    def to_exception(self) -> HTTPError:
        return http_response_to_error(self)


class HTTPSession(Protocol):
    async def request(self, method: str, **opts: Unpack[RequestOpts]) -> HTTPResponse: ...
    async def get(self, **opts: Unpack[RequestOpts]) -> HTTPResponse: ...
    async def post(self, **opts: Unpack[RequestOpts]) -> HTTPResponse: ...
    async def put(self, **opts: Unpack[RequestOpts]) -> HTTPResponse: ...
    async def patch(self, **opts: Unpack[RequestOpts]) -> HTTPResponse: ...
    async def delete(self, **opts: Unpack[RequestOpts]) -> HTTPResponse: ...

    async def close(self) -> None: ...

    async def __aenter__(self) -> Self: ...

    async def __aexit__(
        self,
        exc_type: type[BaseException] | None,
        exc_val: BaseException | None,
        exc_tb: object,
    ) -> None: ...
