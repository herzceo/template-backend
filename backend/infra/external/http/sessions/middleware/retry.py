from __future__ import annotations

import asyncio
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from backend.infra.external.http.sessions.base import (
        HTTPResponse,
        Handler,
        Middleware,
        Request,
    )

_DEFAULT_RETRYABLE: frozenset[int] = frozenset({429, 500, 502, 503, 504})


def retry_middleware(
    max_retries: int = 3,
    backoff_base: float = 1.0,
    backoff_factor: float = 2.0,
    retryable_statuses: frozenset[int] = _DEFAULT_RETRYABLE,
) -> Middleware:
    def middleware(next_handler: Handler) -> Handler:
        async def handler(request: Request) -> HTTPResponse:
            response = await next_handler(request)
            for attempt in range(max_retries):
                if response.status not in retryable_statuses:
                    return response
                delay = backoff_base * (backoff_factor**attempt)
                await asyncio.sleep(delay)
                response = await next_handler(request)
            return response

        return handler

    return middleware
