from __future__ import annotations

import asyncio
import logging
from typing import TYPE_CHECKING

from dishka import make_async_container
from prometheus_client import start_http_server

from backend.app.events.v1.handlers import get_defined_event_handlers
from backend.infra.database.psql import ImplDatabase
from backend.infra.database.psql.dbus.executor import HandlerDef, QueueExecutor
from backend.infra.database.psql.engine import create_async_engine, create_async_session_maker

from .ioc import (
    create_email_provider,
    create_event_handlers_provider,
    create_redis_provider,
    create_security_provider,
)

if TYPE_CHECKING:
    from dishka import AsyncContainer

    from backend.app.events.v1.handlers.base import EventHandler
    from backend.app.shared.events.base import BaseEvent
    from backend.infra.database.config import DatabaseConfig
    from backend.infra.database.psql.dbus.config import QueueExecutorConfig
    from backend.infra.database.redis import RedisConfig
    from backend.infra.database.redis.adapters.config import LoginCodeConfig, VerificationConfig
    from backend.infra.external.http.resend.config import ResendConfig

logger = logging.getLogger(__name__)


def build_handlers(container: AsyncContainer) -> dict[str, HandlerDef]:
    registry = get_defined_event_handlers()
    handlers: dict[str, HandlerDef] = {}

    for event_name, handler_cls in registry.items():
        event_type = handler_cls.event_type

        def _bind(cls: type, etype: type[BaseEvent]) -> HandlerDef:
            async def _handler(**kwargs: object) -> None:
                async with container() as request_container:
                    instance: EventHandler[BaseEvent] = await request_container.get(cls)
                    event = etype.from_builtins(kwargs)
                    await instance(event)

            hdef = HandlerDef()
            hdef.handler = _handler
            return hdef

        handlers[event_name] = _bind(handler_cls, event_type)

    return handlers


def run_queue(
    config: QueueExecutorConfig,
    db_config: DatabaseConfig,
    resend_config: ResendConfig,
    redis_config: RedisConfig,
    verification_config: VerificationConfig,
    login_code_config: LoginCodeConfig,
) -> None:
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s %(levelname)-8s %(name)s: %(message)s",
    )
    asyncio.run(
        _run(config, db_config, resend_config, redis_config, verification_config, login_code_config)
    )


async def _run(
    config: QueueExecutorConfig,
    db_config: DatabaseConfig,
    resend_config: ResendConfig,
    redis_config: RedisConfig,
    verification_config: VerificationConfig,
    login_code_config: LoginCodeConfig,
) -> None:
    start_http_server(config.WORKER_METRICS_PORT)

    engine = create_async_engine(db_config)
    session_maker = create_async_session_maker(engine)
    db = ImplDatabase(session_maker)

    container = make_async_container(
        create_security_provider(),
        create_redis_provider(redis_config, verification_config, login_code_config),
        create_email_provider(resend_config, from_email="noreply@yourdomain.com"),
        create_event_handlers_provider(),
    )

    executor = QueueExecutor(
        config=config,
        db=db,
        engine=engine,
        handlers=build_handlers(container),
    )
    try:
        await executor.run()
    finally:
        await db.close()
        await container.close()
        await engine.dispose()
