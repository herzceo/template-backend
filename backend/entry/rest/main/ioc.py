from __future__ import annotations

from typing import TYPE_CHECKING

from aiobotocore.session import get_session
from dishka import AsyncContainer, Provider, Scope, make_async_container
from sqlalchemy.ext.asyncio import AsyncEngine, AsyncSession, async_sessionmaker

if TYPE_CHECKING:
    from collections.abc import AsyncIterator

    from backend.infra.database.redis import RedisConfig
    from backend.infra.external.http.discord.config import DiscordOAuthSettings
    from backend.infra.external.http.github.config import GitHubOAuthSettings
    from backend.infra.external.http.google_oauth.config import GoogleOAuthSettings
    from backend.infra.security.config import OAuthStateConfig

from backend.app.ports.dbus import DBus
from backend.app.ports.oauth_gateway import OAuthGateway
from backend.app.ports.oauth_state import OAuthStateSigner
from backend.app.ports.password_hasher import PasswordHasher
from backend.app.ports.secret_token import SecretTokenGenerator
from backend.app.ports.verification import VerificationCodeStore
from backend.app.rest.v1 import handlers
from backend.app.rest.v1.services.identity import IdentityService
from backend.app.rest.v1.services.session import SessionService
from backend.domain.repos.database import Database
from backend.infra.database.config import DatabaseConfig
from backend.infra.database.psql.engine import (
    create_async_engine,
    create_async_session_maker,
)
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
from backend.infra.external.http.amplitude.config import AmplitudeSettings
from backend.infra.external.http.discord import DiscordOAuthClient
from backend.infra.external.http.github import GitHubOAuthClient
from backend.infra.external.http.google_maps.client import GoogleMapsClient
from backend.infra.external.http.google_maps.config import GoogleMapsSettings
from backend.infra.external.http.google_oauth import GoogleOAuthClient
from backend.infra.external.http.sessions.aiohttp import (
    AiohttpConfig,
    create_aiohttp_session,
)
from backend.infra.external.s3.client import S3Client
from backend.infra.external.s3.config import S3Settings
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


def create_database_provider() -> Provider:
    provider = Provider(scope=Scope.REQUEST)
    provider.provide(ImplDatabase, provides=Database)
    return provider


def _create_google_oauth_client(settings: GoogleOAuthSettings) -> GoogleOAuthClient:
    session = create_aiohttp_session(AiohttpConfig(BASE_URL="https://oauth2.googleapis.com"))
    return GoogleOAuthClient(session=session, settings=settings)


def _create_github_client(settings: GitHubOAuthSettings) -> GitHubOAuthClient:
    session = create_aiohttp_session(AiohttpConfig(BASE_URL="https://api.github.com"))
    return GitHubOAuthClient(session=session, settings=settings)


def _create_discord_client(settings: DiscordOAuthSettings) -> DiscordOAuthClient:
    session = create_aiohttp_session(AiohttpConfig(BASE_URL="https://discord.com"))
    return DiscordOAuthClient(session=session, settings=settings)


def create_auth_provider(
    *,
    oauth_state_config: OAuthStateConfig,
    google_oauth_settings: GoogleOAuthSettings,
    github_settings: GitHubOAuthSettings,
    discord_settings: DiscordOAuthSettings,
) -> Provider:
    provider = Provider(scope=Scope.APP)
    provider.provide(ImplSHA256SecretTokenGenerator, provides=SecretTokenGenerator)
    provider.provide(ImplArgon2PasswordHasher, provides=PasswordHasher)
    provider.provide(SessionService, provides=SessionService, scope=Scope.REQUEST)

    gateway = ImplOAuthGateway(
        google=ImplGoogleOAuthAdapter(
            _create_google_oauth_client(google_oauth_settings),
            google_oauth_settings,
        ),
        github=ImplGitHubOAuthAdapter(
            _create_github_client(github_settings),
            github_settings,
        ),
        discord=ImplDiscordOAuthAdapter(
            _create_discord_client(discord_settings),
            discord_settings,
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


def _create_amplitude_client(settings: AmplitudeSettings) -> AmplitudeClient:
    session = create_aiohttp_session(AiohttpConfig(BASE_URL=settings.AMPLITUDE_BASE_URL))
    return AmplitudeClient(session=session, settings=settings)


def _create_google_maps_client(settings: GoogleMapsSettings) -> GoogleMapsClient:
    session = create_aiohttp_session(AiohttpConfig(BASE_URL=settings.GOOGLE_MAPS_BASE_URL))
    return GoogleMapsClient(session=session, settings=settings)


async def _create_s3_client(settings: S3Settings) -> AsyncIterator[S3Client]:
    session = get_session()
    async with session.create_client(
        "s3",
        region_name=settings.S3_REGION,
        aws_access_key_id=settings.S3_ACCESS_KEY_ID,
        aws_secret_access_key=settings.S3_SECRET_ACCESS_KEY,
        endpoint_url=settings.S3_ENDPOINT_URL,
    ) as client:
        yield S3Client(settings=settings, client=client)


def create_external_provider(
    *,
    amplitude_settings: AmplitudeSettings | None = None,
    google_maps_settings: GoogleMapsSettings | None = None,
    s3_settings: S3Settings | None = None,
) -> Provider:
    provider = Provider(scope=Scope.APP)

    if amplitude_settings is not None:
        provider.provide(lambda: amplitude_settings, provides=AmplitudeSettings)
        provider.provide(_create_amplitude_client, provides=AmplitudeClient)

    if google_maps_settings is not None:
        provider.provide(lambda: google_maps_settings, provides=GoogleMapsSettings)
        provider.provide(_create_google_maps_client, provides=GoogleMapsClient)

    if s3_settings is not None:
        provider.provide(lambda: s3_settings, provides=S3Settings)
        provider.provide(_create_s3_client, provides=S3Client)

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
    google_oauth_settings: GoogleOAuthSettings,
    github_settings: GitHubOAuthSettings,
    discord_settings: DiscordOAuthSettings,
    amplitude_settings: AmplitudeSettings | None = None,
    google_maps_settings: GoogleMapsSettings | None = None,
    s3_settings: S3Settings | None = None,
) -> AsyncContainer:
    return make_async_container(
        create_utils_provider(db_config),
        create_psql_provider(),
        create_database_provider(),
        create_dbus_provider(),
        create_redis_provider(redis_config, verification_config),
        create_auth_provider(
            oauth_state_config=oauth_state_config,
            google_oauth_settings=google_oauth_settings,
            github_settings=github_settings,
            discord_settings=discord_settings,
        ),
        create_handlers_provider(),
        create_external_provider(
            amplitude_settings=amplitude_settings,
            google_maps_settings=google_maps_settings,
            s3_settings=s3_settings,
        ),
    )
