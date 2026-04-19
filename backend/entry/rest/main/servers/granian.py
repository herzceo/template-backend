from __future__ import annotations

from functools import partial
from typing import TYPE_CHECKING

from granian import Granian
from granian.constants import Interfaces
from granian.log import LogLevels

if TYPE_CHECKING:
    from collections.abc import Callable

    from litestar import Litestar

    from backend.entry.rest.main.config import APIConfig


class GranianServer:
    def __init__(
        self,
        app_factory: Callable[[], Litestar],
        api_config: APIConfig,
    ) -> None:
        self._loader = partial(app_factory)
        self._server = Granian(
            target="",
            address=api_config.HOST,
            port=api_config.PORT,
            interface=Interfaces.ASGI,
            log_level=LogLevels(api_config.LOG_LEVEL.lower()),
        )

    def run(self) -> None:
        self._server.serve(target_loader=self._loader, wrap_loader=False)
