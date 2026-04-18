from __future__ import annotations

from typing import TYPE_CHECKING, Any

from .granian import GranianServer
from .type import ServerType
from .uvicorn import UvicornServer

if TYPE_CHECKING:
    from backend.entry.rest.main.config import APIConfig
    from backend.infra.database.config import DatabaseConfig


def create_server(
    api_config: APIConfig,
    db_config: DatabaseConfig,
    **kwargs: Any,
) -> GranianServer | UvicornServer:
    match api_config.SERVER_TYPE:
        case ServerType.GRANIAN:
            return GranianServer(api_config, db_config, **kwargs)
        case ServerType.UVICORN:
            return UvicornServer(api_config, db_config, **kwargs)
