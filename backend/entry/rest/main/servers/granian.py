from __future__ import annotations

from functools import partial
from typing import TYPE_CHECKING, Any

from granian import Granian
from granian.constants import Interfaces
from granian.log import LogLevels

from backend.entry.rest.main.api import create_api

if TYPE_CHECKING:
    from litestar import Litestar

    from backend.entry.rest.main.config import APIConfig
    from backend.infra.database.config import DatabaseConfig


def _build_app(
    api_config: APIConfig,
    db_config: DatabaseConfig,
    **kwargs: Any,
) -> Litestar:
    return create_api(api_config, db_config, **kwargs)


class GranianServer:
    def __init__(
        self,
        api_config: APIConfig,
        db_config: DatabaseConfig,
        **kwargs: Any,
    ) -> None:
        self._loader = partial(_build_app, api_config, db_config, **kwargs)
        self._server = Granian(
            target="",
            address=api_config.HOST,
            port=api_config.PORT,
            interface=Interfaces.ASGI,
            log_level=LogLevels(api_config.LOG_LEVEL.lower()),
        )

    def run(self) -> None:
        self._server.serve(target_loader=self._loader, wrap_loader=False)
