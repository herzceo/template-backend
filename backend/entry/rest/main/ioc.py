from dishka import AsyncContainer, Provider, Scope, make_async_container
from sqlalchemy.ext.asyncio import AsyncEngine, AsyncSession, async_sessionmaker

from backend.app.rest.v1 import handlers
from backend.domain.repos.gateway import RepoGateway
from backend.infra.database.config import DatabaseConfig
from backend.infra.database.psql.engine import (
    create_async_engine,
    create_async_session,
    create_async_session_maker,
)
from backend.infra.database.psql.repos import (
    ImplRepoGateway,
)


def create_utils_provider(db_config: DatabaseConfig) -> Provider:
    provider = Provider(scope=Scope.APP)

    provider.provide(lambda: db_config, provides=DatabaseConfig)

    return provider


def create_psql_provider() -> Provider:
    provider = Provider(scope=Scope.APP)

    provider.provide(create_async_engine, provides=AsyncEngine)
    provider.provide(create_async_session_maker, provides=async_sessionmaker[AsyncSession])
    provider.provide(create_async_session, provides=AsyncSession, scope=Scope.REQUEST)

    return provider


def create_repos_provider() -> Provider:
    provider = Provider(scope=Scope.REQUEST)
    provider.provide(ImplRepoGateway, provides=RepoGateway)
    return provider


def create_handlers_provider() -> Provider:
    provider = Provider(scope=Scope.REQUEST)
    for handler in handlers.get_defined_handlers().values():
        provider.provide(handler, provides=handler)
    return provider


def create_container(db_config: DatabaseConfig) -> AsyncContainer:
    return make_async_container(
        create_utils_provider(db_config),
        create_psql_provider(),
        create_repos_provider(),
        create_handlers_provider(),
    )
