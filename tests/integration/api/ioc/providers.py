from __future__ import annotations

from collections.abc import AsyncIterator

from dishka import AsyncContainer, Provider, Scope, make_async_container
from sqlalchemy.ext.asyncio import AsyncEngine, AsyncSession, async_sessionmaker
from sqlalchemy.ext.asyncio import create_async_engine as _create_async_engine
from sqlalchemy.pool import NullPool

from backend.app.rest.v1.services.identity import IdentityService
from backend.app.rest.v1.services.session import SessionConfig, SessionService
from backend.app.shared.db.database import Database
from backend.app.shared.db.dbus import DBus
from backend.app.shared.db.query_services.gateway import QueryServiceGateway
from backend.app.shared.ports.auth.oauth_gateway import OAuthGateway
from backend.app.shared.ports.auth.oauth_state import OAuthStateSigner
from backend.app.shared.ports.auth.password_hasher import PasswordHasher
from backend.app.shared.ports.outreach.email import EmailSender
from backend.app.shared.ports.security.secret_token import SecretTokenGenerator
from backend.app.shared.ports.security.verification import VerificationCodeStore
from backend.app.shared.ports.storage import ObjectStore
from backend.entry.rest.main.ioc import create_handlers_provider
from backend.infra.database.psql.engine import create_async_session_maker
from backend.infra.database.psql.queries import ImplQueryServiceGateway
from backend.infra.database.psql.repos import ImplDatabase
from backend.infra.security.oauth_state import ImplHMACOAuthStateSigner
from backend.infra.security.password_hasher import ImplArgon2PasswordHasher
from backend.infra.security.secret_token import ImplSHA256SecretTokenGenerator
from tests.integration.mocks import (
    MockDBus,
    MockEmailSender,
    MockOAuthGateway,
    MockObjectStore,
    MockVerificationCodeStore,
)


def _create_session_service(
    db: Database, token_generator: SecretTokenGenerator, session_config: SessionConfig
) -> SessionService:
    return SessionService(db=db, token_generator=token_generator, session_config=session_config)


async def _create_test_database(
    session_maker: async_sessionmaker[AsyncSession],
) -> AsyncIterator[ImplDatabase]:
    db = ImplDatabase(session_maker)
    try:
        yield db
    finally:
        await db.close()


def _database_alias(db: ImplDatabase) -> Database:
    return db


def create_test_container(*, postgres_url: str) -> AsyncContainer:
    mock_email = MockEmailSender()
    mock_dbus = MockDBus()
    mock_object_store = MockObjectStore()
    mock_oauth = MockOAuthGateway()
    mock_verification = MockVerificationCodeStore()

    mocks_provider = Provider(scope=Scope.APP)
    mocks_provider.provide(lambda: mock_email, provides=EmailSender)
    mocks_provider.provide(lambda: mock_dbus, provides=DBus)
    mocks_provider.provide(lambda: mock_object_store, provides=ObjectStore)
    mocks_provider.provide(lambda: mock_oauth, provides=OAuthGateway)
    mocks_provider.provide(lambda: mock_verification, provides=VerificationCodeStore)

    engine = _create_async_engine(postgres_url, poolclass=NullPool)
    session_maker = create_async_session_maker(engine)

    db_provider = Provider(scope=Scope.APP)
    db_provider.provide(lambda: engine, provides=AsyncEngine)
    db_provider.provide(lambda: session_maker, provides=async_sessionmaker[AsyncSession])

    req_provider = Provider(scope=Scope.REQUEST)
    req_provider.provide(_create_test_database, provides=ImplDatabase)
    req_provider.provide(_database_alias, provides=Database)
    req_provider.provide(ImplQueryServiceGateway, provides=QueryServiceGateway)

    state_signer = ImplHMACOAuthStateSigner(secret="test-oauth-state-secret-for-testing")
    session_config = SessionConfig()

    auth_provider = Provider(scope=Scope.APP)
    auth_provider.provide(ImplArgon2PasswordHasher, provides=PasswordHasher)
    auth_provider.provide(ImplSHA256SecretTokenGenerator, provides=SecretTokenGenerator)
    auth_provider.provide(lambda: state_signer, provides=OAuthStateSigner)
    auth_provider.provide(lambda: session_config, provides=SessionConfig)

    services_provider = Provider(scope=Scope.REQUEST)
    services_provider.provide(_create_session_service, provides=SessionService)
    services_provider.provide(IdentityService, provides=IdentityService)

    return make_async_container(
        db_provider,
        req_provider,
        mocks_provider,
        auth_provider,
        services_provider,
        create_handlers_provider(),
    )
