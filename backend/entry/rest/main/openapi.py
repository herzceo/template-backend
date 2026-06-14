from litestar.openapi.config import OpenAPIConfig

from .config import APIConfig
from .scalar import RelativeScalarRenderPlugin


def create_openapi(config: APIConfig) -> OpenAPIConfig | None:
    return (
        OpenAPIConfig(
            title=config.NAME,
            description=config.DESCRIPTION,
            version=config.VERSION,
            path=config.OPENAPI_PATH,
            render_plugins=[RelativeScalarRenderPlugin(version=config.SCALAR_VERSION)],
        )
        if config.OPENAPI_EXISTS
        else None
    )
