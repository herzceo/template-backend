from __future__ import annotations

from datetime import timedelta
from typing import TYPE_CHECKING

from aiobotocore.session import get_session
from dishka import AsyncContainer, Provider, Scope, make_async_container
from sqlalchemy.ext.asyncio import AsyncEngine, AsyncSession, async_sessionmaker

if TYPE_CHECKING:
    from collections.abc import AsyncIterator

    from backend.infra.database.redis import RedisConfig
    from backend.infra.external.http.discord.config import DiscordOAuthConfig
    from backend.infra.external.http.github.config import GitHubOAuthConfig
    from backend.infra.external.http.google_oauth.config import GoogleOAuthConfig
    from backend.infra.security.config import OAuthStateConfig

from backend.app.rest.v1 import handlers
from backend.app.rest.v1.services.identity import IdentityService
from backend.app.rest.v1.services.session import SessionService
from backend.app.shared.ports.auth.oauth_gateway import OAuthGateway
from backend.app.shared.ports.auth.oauth_state import OAuthStateSigner
from backend.app.shared.ports.auth.password_hasher import PasswordHasher
from backend.app.shared.ports.events.dbus import DBus
from backend.app.shared.ports.security.secret_token import SecretTokenGenerator
from backend.app.shared.ports.security.verification import VerificationCodeStore
from backend.app.shared.ports.storage import ObjectStore
from backend.app.shared.query_services.gateway import QueryServiceGateway
from backend.domain.repos.database import Database
from backend.infra.database.config import DatabaseConfig
from backend.infra.database.object import S3ObjectStore
from backend.infra.database.psql.engine import (
    create_async_engine,
    create_async_session_maker,
)
from backend.infra.database.psql.queries import ImplQueryServiceGateway
from backend.infra.database.psql.repos import ImplDatabase
from backend.infra.database.redis import RedisClient
from backend.infra.database.redis.adapters.config import VerificationConfig
from backend.infra.database.redis.adapters.verification_code import ImplVerificationCodeStore
from backend.infra.dbus.psql import ImplDBus
from backend.infra.external.adapters.oauth import (
    ImplDiscordOAuthAdapter,
    ImplGitHubOAuthAdapter,
    ImplGoogleOAuthAdapter,
    ImplOAuthGateway,
)
from backend.infra.external.http.amplitude.client import AmplitudeClient
from backend.infra.external.http.amplitude.config import AmplitudeConfig
from backend.infra.external.http.discord import DiscordOAuthClient
from backend.infra.external.http.github import GitHubOAuthClient
from backend.infra.external.http.google_maps.client import GoogleMapsClient
from backend.infra.external.http.google_maps.config import GoogleMapsConfig
from backend.infra.external.http.google_oauth import GoogleOAuthClient
from backend.infra.external.http.sessions.aiohttp import (
    AiohttpConfig,
    create_aiohttp_session,
)
from backend.infra.external.s3.client import S3Client
from backend.infra.external.s3.config import S3Config
from backend.infra.security.oauth_state import ImplHMACOAuthStateSigner
from backend.infra.security.password_hasher import ImplArgon2PasswordHasher
from backend.infra.security.secret_token import ImplSHA256SecretTokenGenerator


def create_utils_provider(db_config: DatabaseConfig) -> Provider:
    provider = Provider(scope=Scope.APP)
    provider.provide(lambda: db_config, provides=DatabaseConfig)
    return provider


def create_psql_provider() -> Provider:
    provider = Provider(scope=Scope.APP)
    provider.provide(create_async_engine, provides=AsyncEngine)
    provider.provide(create_async_session_maker, provides=async_sessionmaker[AsyncSession])
    return provider


def _create_database(session_maker: async_sessionmaker[AsyncSession]) -> ImplDatabase:
    return ImplDatabase(session_maker)


def create_database_provider() -> Provider:
    provider = Provider(scope=Scope.REQUEST)
    provider.provide(_create_database, provides=Database)
    return provider


def create_query_services_provider() -> Provider:
    provider = Provider(scope=Scope.REQUEST)
    provider.provide(ImplQueryServiceGateway, provides=QueryServiceGateway)
    return provider


def _create_google_oauth_client(config: GoogleOAuthConfig) -> GoogleOAuthClient:
    session = create_aiohttp_session(AiohttpConfig(BASE_URL="https://oauth2.googleapis.com"))
    return GoogleOAuthClient(session=session, config=config)


def _create_github_client(config: GitHubOAuthConfig) -> GitHubOAuthClient:
    session = create_aiohttp_session(AiohttpConfig(BASE_URL="https://api.github.com"))
    return GitHubOAuthClient(session=session, config=config)


def _create_discord_client(config: DiscordOAuthConfig) -> DiscordOAuthClient:
    session = create_aiohttp_session(AiohttpConfig(BASE_URL="https://discord.com"))
    return DiscordOAuthClient(session=session, config=config)


def _create_session_service(db: Database, token_generator: SecretTokenGenerator) -> SessionService:
    return SessionService(db=db, token_generator=token_generator, session_ttl=timedelta(days=14))


def create_auth_provider(
    *,
    oauth_state_config: OAuthStateConfig,
    google_oauth_config: GoogleOAuthConfig,
    github_config: GitHubOAuthConfig,
    discord_config: DiscordOAuthConfig,
) -> Provider:
    provider = Provider(scope=Scope.APP)
    provider.provide(ImplSHA256SecretTokenGenerator, provides=SecretTokenGenerator)
    provider.provide(ImplArgon2PasswordHasher, provides=PasswordHasher)
    provider.provide(_create_session_service, provides=SessionService, scope=Scope.REQUEST)

    gateway = ImplOAuthGateway(
        google=ImplGoogleOAuthAdapter(
            _create_google_oauth_client(google_oauth_config),
            google_oauth_config,
        ),
        github=ImplGitHubOAuthAdapter(
            _create_github_client(github_config),
            github_config,
        ),
        discord=ImplDiscordOAuthAdapter(
            _create_discord_client(discord_config),
            discord_config,
        ),
    )
    state_signer = ImplHMACOAuthStateSigner(secret=oauth_state_config.OAUTH_STATE_SECRET)

    provider.provide(lambda: gateway, provides=OAuthGateway)
    provider.provide(lambda: state_signer, provides=OAuthStateSigner)
    provider.provide(IdentityService, provides=IdentityService, scope=Scope.REQUEST)

    return provider


def create_handlers_provider() -> Provider:
    provider = Provider(scope=Scope.REQUEST)
    for handler in handlers.get_defined_rest_handlers().values():
        provider.provide(handler, provides=handler)
    return provider


def _create_amplitude_client(config: AmplitudeConfig) -> AmplitudeClient:
    session = create_aiohttp_session(AiohttpConfig(BASE_URL=config.AMPLITUDE_BASE_URL))
    return AmplitudeClient(session=session, config=config)


def _create_google_maps_client(config: GoogleMapsConfig) -> GoogleMapsClient:
    session = create_aiohttp_session(AiohttpConfig(BASE_URL=config.GOOGLE_MAPS_BASE_URL))
    return GoogleMapsClient(session=session, config=config)


async def _create_s3_client(config: S3Config) -> AsyncIterator[S3Client]:
    session = get_session()
    async with session.create_client(
        "s3",
        region_name=config.S3_REGION,
        aws_access_key_id=config.S3_ACCESS_KEY_ID,
        aws_secret_access_key=config.S3_SECRET_ACCESS_KEY,
        endpoint_url=config.S3_ENDPOINT_URL,
    ) as client:
        yield S3Client(config=config, client=client)


def create_external_provider(
    *,
    amplitude_config: AmplitudeConfig | None = None,
    google_maps_config: GoogleMapsConfig | None = None,
    s3_config: S3Config | None = None,
) -> Provider:
    provider = Provider(scope=Scope.APP)

    if amplitude_config is not None:
        provider.provide(lambda: amplitude_config, provides=AmplitudeConfig)
        provider.provide(_create_amplitude_client, provides=AmplitudeClient)

    if google_maps_config is not None:
        provider.provide(lambda: google_maps_config, provides=GoogleMapsConfig)
        provider.provide(_create_google_maps_client, provides=GoogleMapsClient)

    if s3_config is not None:
        provider.provide(lambda: s3_config, provides=S3Config)
        provider.provide(_create_s3_client, provides=S3Client)
        provider.provide(S3ObjectStore, provides=ObjectStore)

    return provider


def create_dbus_provider() -> Provider:
    provider = Provider(scope=Scope.REQUEST)
    provider.provide(ImplDBus, provides=DBus)
    return provider


def create_redis_provider(
    redis_config: RedisConfig, verification_config: VerificationConfig
) -> Provider:
    provider = Provider(scope=Scope.APP)
    provider.provide(lambda: redis_config, provides=type(redis_config))
    provider.provide(lambda: verification_config, provides=VerificationConfig)
    provider.provide(RedisClient, provides=RedisClient)
    provider.provide(ImplVerificationCodeStore, provides=VerificationCodeStore)
    return provider


def create_container(
    db_config: DatabaseConfig,
    *,
    redis_config: RedisConfig,
    verification_config: VerificationConfig,
    oauth_state_config: OAuthStateConfig,
    google_oauth_config: GoogleOAuthConfig,
    github_config: GitHubOAuthConfig,
    discord_config: DiscordOAuthConfig,
    amplitude_config: AmplitudeConfig | None = None,
    google_maps_config: GoogleMapsConfig | None = None,
    s3_config: S3Config | None = None,
) -> AsyncContainer:
    return make_async_container(
        create_utils_provider(db_config),
        create_psql_provider(),
        create_database_provider(),
        create_query_services_provider(),
        create_dbus_provider(),
        create_redis_provider(redis_config, verification_config),
        create_auth_provider(
            oauth_state_config=oauth_state_config,
            google_oauth_config=google_oauth_config,
            github_config=github_config,
            discord_config=discord_config,
        ),
        create_handlers_provider(),
        create_external_provider(
            amplitude_config=amplitude_config,
            google_maps_config=google_maps_config,
            s3_config=s3_config,
        ),
    )
