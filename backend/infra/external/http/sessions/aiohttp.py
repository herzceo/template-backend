from __future__ import annotations

from typing import TYPE_CHECKING, Self, Unpack
from urllib.parse import urljoin

import aiohttp

from backend.infra.external.errors import NetworkError
from backend.infra.external.http.sessions.base import (
    HTTPResponse,
    Request,
    RequestOpts,
)
from backend.internal.dto import StructDTO

if TYPE_CHECKING:
    from collections.abc import Sequence

    from backend.infra.external.http.sessions.base import Handler, Middleware


class AiohttpConfig(StructDTO):
    BASE_URL: str
    TIMEOUT: int = 30
    MAX_CONNECTIONS: int = 100
    MAX_CONNECTIONS_PER_HOST: int = 30
    DNS_CACHE_TTL: int = 300
    KEEPALIVE_TIMEOUT: int = 120
    SSL_VERIFY: bool = True


class AiohttpSession:
    __slots__ = ("_base_url", "_middlewares", "_session")

    def __init__(
        self,
        session: aiohttp.ClientSession,
        base_url: str,
        middlewares: Sequence[Middleware] = (),
    ) -> None:
        self._session = session
        self._base_url = base_url.rstrip("/")
        self._middlewares = middlewares

    def _resolve_url(self, url: str) -> str:
        if url.startswith(("http://", "https://")):
            return url
        return urljoin(self._base_url + "/", url.lstrip("/"))

    async def _raw_request(self, request: Request) -> HTTPResponse:
        resolved_url = self._resolve_url(request.url)
        timeout = aiohttp.ClientTimeout(total=t) if (t := request.timeout) else None

        try:
            async with self._session.request(
                request.method,
                resolved_url,
                headers=request.headers or None,
                params=request.params or None,
                json=request.json,
                data=request.data,
                timeout=timeout,
            ) as resp:
                body = await resp.read()
                return HTTPResponse(
                    status=resp.status,
                    url=str(resp.url),
                    headers=dict(resp.headers.items()),
                    body=body,
                )
        except (TimeoutError, aiohttp.ClientError) as e:
            raise NetworkError(
                message=f"Connection error: {request.method} {resolved_url}: {e}",
                details={
                    "method": request.method,
                    "url": resolved_url,
                    "error_type": type(e).__name__,
                },
            ) from e

    async def request(
        self,
        method: str,
        **opts: Unpack[RequestOpts],
    ) -> HTTPResponse:
        middlewares = opts.pop("middlewares", ())
        req = Request(method=method, **opts)  # type: ignore[misc]
        handler: Handler = self._raw_request
        for mw in reversed([*self._middlewares, *middlewares]):
            handler = mw(handler)
        return await handler(req)

    async def get(self, **opts: Unpack[RequestOpts]) -> HTTPResponse:
        return await self.request("GET", **opts)

    async def post(self, **opts: Unpack[RequestOpts]) -> HTTPResponse:
        return await self.request("POST", **opts)

    async def put(self, **opts: Unpack[RequestOpts]) -> HTTPResponse:
        return await self.request("PUT", **opts)

    async def patch(self, **opts: Unpack[RequestOpts]) -> HTTPResponse:
        return await self.request("PATCH", **opts)

    async def delete(self, **opts: Unpack[RequestOpts]) -> HTTPResponse:
        return await self.request("DELETE", **opts)

    async def close(self) -> None:
        if not self._session.closed:
            await self._session.close()

    async def __aenter__(self) -> Self:
        return self

    async def __aexit__(
        self,
        exc_type: type[BaseException] | None,
        exc_val: BaseException | None,
        exc_tb: object,
    ) -> None:
        await self.close()


def create_aiohttp_session(
    config: AiohttpConfig,
    middlewares: Sequence[Middleware] = (),
) -> AiohttpSession:
    connector = aiohttp.TCPConnector(
        limit=config.MAX_CONNECTIONS,
        limit_per_host=config.MAX_CONNECTIONS_PER_HOST,
        ttl_dns_cache=config.DNS_CACHE_TTL,
        keepalive_timeout=config.KEEPALIVE_TIMEOUT,
        ssl=None if config.SSL_VERIFY else False,  # type: ignore[arg-type]
    )
    timeout = aiohttp.ClientTimeout(total=config.TIMEOUT)
    session = aiohttp.ClientSession(connector=connector, timeout=timeout)
    return AiohttpSession(session=session, base_url=config.BASE_URL, middlewares=middlewares)
