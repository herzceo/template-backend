from functools import partial

from granian import Granian
from granian.constants import Interfaces
from granian.log import LogLevels
from litestar import Litestar

from backend.entry.rest.main.api import create_api
from backend.entry.rest.main.config import APIConfig
from backend.infra.database.config import DatabaseConfig


def _build_app(api_config: APIConfig, db_config: DatabaseConfig) -> Litestar:
    return create_api(api_config, db_config)


class GranianServer:
    def __init__(self, api_config: APIConfig, db_config: DatabaseConfig) -> None:
        self._loader = partial(_build_app, api_config, db_config)
        self._server = Granian(
            target="",
            address=api_config.HOST,
            port=api_config.PORT,
            interface=Interfaces.ASGI,
            log_level=LogLevels(api_config.LOG_LEVEL.lower()),
        )

    def run(self) -> None:
        self._server.serve(target_loader=self._loader, wrap_loader=False)
