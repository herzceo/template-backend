from __future__ import annotations

from typing import TYPE_CHECKING, Any

import pytest
from dishka import AsyncContainer
from dishka.integrations.litestar import setup_dishka
from litestar import Litestar, Router
from litestar.middleware.base import DefineMiddleware
from litestar.testing import AsyncTestClient

from backend.entry.rest.common.middlewares.session import SessionMiddleware
from backend.entry.rest.main.config import APIConfig
from backend.entry.rest.main.cors import create_cors
from backend.entry.rest.main.exc import create_exception_handlers
from backend.entry.rest.main.openapi import create_openapi
from backend.entry.rest.main.servers.type import ServerType
from backend.entry.rest.v1 import create_v1_router
from tests.integration.api.factories.tenant import create_tenant
from tests.integration.api.factories.user import create_logged_user, create_user
from tests.integration.api.ioc.providers import create_test_container

if TYPE_CHECKING:
    from collections.abc import AsyncIterator

    from backend.domain.entities.tenant import Tenant
    from backend.domain.entities.user import User


def _make_api_config() -> APIConfig:
    return APIConfig(
        NAME="Test API",
        DESCRIPTION="Integration tests",
        VERSION="0.0.1",
        LOG_LEVEL="DEBUG",
        HOST="localhost",
        PORT=8000,
        SCALAR_VERSION="latest",
        OPENAPI_PATH="/schema",
        OPENAPI_EXISTS=True,
        CORS_ALLOW_ORIGINS=["http://testserver"],
        CORS_ALLOW_HEADERS=["*"],
        CORS_ALLOW_METHODS=["GET", "POST", "DELETE", "PATCH", "PUT", "HEAD", "OPTIONS"],
        CORS_EXPOSE_HEADERS=[],
        CORS_MAX_AGE=0,
        SERVER_TYPE=ServerType.GRANIAN,
    )


def _make_litestar_app(container: AsyncContainer) -> Litestar:
    config = _make_api_config()
    app = Litestar(
        path="",
        route_handlers=[Router("", route_handlers=[create_v1_router()])],
        middleware=[DefineMiddleware(SessionMiddleware)],
        openapi_config=create_openapi(config),
        cors_config=create_cors(config),
        exception_handlers=create_exception_handlers(),
    )
    setup_dishka(container=container, app=app)
    return app


@pytest.fixture
async def container(postgres_url: str) -> AsyncIterator[AsyncContainer]:
    c = create_test_container(postgres_url=postgres_url)
    try:
        yield c
    finally:
        await c.close()


@pytest.fixture
async def client(container: AsyncContainer) -> AsyncIterator[AsyncTestClient[Any]]:
    app = _make_litestar_app(container)
    async with AsyncTestClient(app=app, base_url="http://testserver") as c:
        yield c


@pytest.fixture
async def tenant(container: AsyncContainer) -> Tenant:
    return await create_tenant(container)


@pytest.fixture
async def user(container: AsyncContainer, tenant: Tenant) -> User:
    return await create_user(container, tenant.id)


@pytest.fixture
async def auth_user(
    client: AsyncTestClient[Any],
    container: AsyncContainer,
    tenant: Tenant,
) -> User:
    return await create_logged_user(client, container, tenant.id)
