from dishka.integrations.litestar import setup_dishka
from litestar import Litestar, Router
from litestar.middleware.base import DefineMiddleware

from backend.entry.rest.common.middlewares.session import SessionMiddleware
from backend.entry.rest.v1 import create_v1_router
from backend.infra.database.config import DatabaseConfig

from .config import APIConfig
from .cors import create_cors
from .exc import create_exception_handlers
from .ioc import create_container
from .openapi import create_openapi
from .servers.factory import create_server


def create_router() -> Router:
    return Router("", route_handlers=[create_v1_router()])


def create_api(config: APIConfig, db_config: DatabaseConfig) -> Litestar:
    app = Litestar(
        path="",
        route_handlers=[create_router()],
        middleware=[DefineMiddleware(SessionMiddleware)],
        openapi_config=create_openapi(config),
        cors_config=create_cors(config),
        exception_handlers=create_exception_handlers(),
        debug=config.LOG_LEVEL == "DEBUG",
    )

    setup_dishka(container=create_container(db_config), app=app)
    return app


def run_api(config: APIConfig, db_config: DatabaseConfig) -> None:
    create_server(config, db_config).run()
