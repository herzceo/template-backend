from uvicorn import Config, Server

from backend.entry.rest.main.api import create_api
from backend.entry.rest.main.config import APIConfig
from backend.infra.database.config import DatabaseConfig


class UvicornServer:
    def __init__(self, api_config: APIConfig, db_config: DatabaseConfig) -> None:
        self._server = Server(
            Config(
                create_api(api_config, db_config),
                host=api_config.HOST,
                port=api_config.PORT,
                log_level=api_config.LOG_LEVEL.lower(),
            )
        )

    def run(self) -> None:
        self._server.run()
