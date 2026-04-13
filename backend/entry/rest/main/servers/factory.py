from backend.entry.rest.main.config import APIConfig
from backend.infra.database.config import DatabaseConfig

from .granian import GranianServer
from .type import ServerType
from .uvicorn import UvicornServer


def create_server(
    api_config: APIConfig, db_config: DatabaseConfig
) -> GranianServer | UvicornServer:
    match api_config.SERVER_TYPE:
        case ServerType.GRANIAN:
            return GranianServer(api_config, db_config)
        case ServerType.UVICORN:
            return UvicornServer(api_config, db_config)
