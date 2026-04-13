from typing import Literal

from backend.internal.dto import StructDTO

from .servers import ServerType


class APIConfig(StructDTO):
    NAME: str
    DESCRIPTION: str
    VERSION: str
    LOG_LEVEL: Literal["DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"]
    HOST: str
    PORT: int

    SCALAR_VERSION: str
    OPENAPI_PATH: str
    OPENAPI_EXISTS: bool

    CORS_ALLOW_ORIGINS: list[str]
    CORS_ALLOW_HEADERS: list[str]
    CORS_ALLOW_METHODS: list[
        Literal["*", "GET", "POST", "DELETE", "PATCH", "PUT", "HEAD", "TRACE", "OPTIONS"]
    ]
    CORS_EXPOSE_HEADERS: list[str]
    CORS_MAX_AGE: int

    SERVER_TYPE: ServerType = ServerType.GRANIAN
