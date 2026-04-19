from dishka import Provider, Scope

from backend.app.events.v1.handlers import get_defined_event_handlers
from backend.app.ports.email import EmailSender
from backend.app.ports.secret_token import SecretTokenGenerator
from backend.app.ports.verification import VerificationCodeStore
from backend.infra.database.redis import RedisClient
from backend.infra.database.redis.adapters.config import VerificationConfig
from backend.infra.database.redis.adapters.verification_code import ImplVerificationCodeStore
from backend.infra.database.redis.config import RedisConfig
from backend.infra.external.adapters.email import ImplResendEmailSender
from backend.infra.external.http.resend.client import ResendClient
from backend.infra.external.http.resend.config import ResendSettings
from backend.infra.external.http.sessions.aiohttp import AiohttpConfig, create_aiohttp_session
from backend.infra.security.secret_token import ImplSHA256SecretTokenGenerator


def create_security_provider() -> Provider:
    provider = Provider(scope=Scope.APP)
    provider.provide(ImplSHA256SecretTokenGenerator, provides=SecretTokenGenerator)
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


def create_event_handlers_provider() -> Provider:
    provider = Provider(scope=Scope.REQUEST)
    for handler_cls in get_defined_event_handlers().values():
        provider.provide(handler_cls, provides=handler_cls)
    return provider


def create_email_provider(resend_settings: ResendSettings, from_email: str) -> Provider:
    provider = Provider(scope=Scope.APP)
    session = create_aiohttp_session(AiohttpConfig(BASE_URL=resend_settings.RESEND_BASE_URL))
    client = ResendClient(session=session, settings=resend_settings)
    sender = ImplResendEmailSender(client, from_email=from_email)
    provider.provide(lambda: sender, provides=EmailSender)
    return provider
