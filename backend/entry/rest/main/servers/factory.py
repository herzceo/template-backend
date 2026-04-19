from __future__ import annotations

from typing import TYPE_CHECKING

from .granian import GranianServer
from .type import ServerType
from .uvicorn import UvicornServer

if TYPE_CHECKING:
    from collections.abc import Callable

    from litestar import Litestar

    from backend.entry.rest.main.config import APIConfig


def create_server(
    app_factory: Callable[[], Litestar],
    api_config: APIConfig,
) -> GranianServer | UvicornServer:
    match api_config.SERVER_TYPE:
        case ServerType.GRANIAN:
            return GranianServer(app_factory, api_config)
        case ServerType.UVICORN:
            return UvicornServer(app_factory(), api_config)
