from __future__ import annotations

import logging
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from backend.infra.external.http.sessions.base import (
        HTTPResponse,
        Handler,
        Middleware,
        Request,
    )

_default_logger = logging.getLogger("backend.infra.external")


def logging_middleware(
    logger: logging.Logger | None = None,
    level: int = logging.DEBUG,
) -> Middleware:
    log = logger or _default_logger

    def middleware(next_handler: Handler) -> Handler:
        async def handler(request: Request) -> HTTPResponse:
            log.log(level, "-> %s %s", request.method, request.url)
            response = await next_handler(request)
            log.log(level, "<- %s %s %d", request.method, request.url, response.status)
            return response

        return handler

    return middleware
