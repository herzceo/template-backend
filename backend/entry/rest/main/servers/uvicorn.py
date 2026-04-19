from __future__ import annotations

from typing import TYPE_CHECKING

from uvicorn import Config, Server

if TYPE_CHECKING:
    from litestar import Litestar

    from backend.entry.rest.main.config import APIConfig


class UvicornServer:
    def __init__(
        self,
        app: Litestar,
        api_config: APIConfig,
    ) -> None:
        self._server = Server(
            Config(
                app,
                host=api_config.HOST,
                port=api_config.PORT,
                log_level=api_config.LOG_LEVEL.lower(),
            )
        )

    def run(self) -> None:
        self._server.run()
