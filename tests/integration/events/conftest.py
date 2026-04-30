from __future__ import annotations

from collections.abc import Awaitable
from typing import TYPE_CHECKING

import pytest
from sqlalchemy.ext.asyncio import create_async_engine as _create_async_engine
from sqlalchemy.pool import NullPool

from backend.entry.queue.main import build_handlers
from backend.infra.database.psql.engine import create_async_session_maker
from backend.infra.database.psql.repos import ImplDatabase
from backend.infra.dbus.psql.config import QueueExecutorConfig
from backend.infra.dbus.psql.dbus import ImplDBus
from backend.infra.dbus.psql.executor import QueueExecutor
from tests.integration.events.ioc.providers import create_test_queue_container

if TYPE_CHECKING:
    from collections.abc import AsyncIterator, Callable

    from dishka import AsyncContainer

    from backend.app.shared.events.base import BaseEvent


@pytest.fixture
async def queue_container() -> AsyncIterator[AsyncContainer]:
    c = create_test_queue_container()
    try:
        yield c
    finally:
        await c.close()


@pytest.fixture
async def executor(
    queue_container: AsyncContainer,
    postgres_url: str,
) -> AsyncIterator[QueueExecutor]:
    engine = _create_async_engine(postgres_url, poolclass=NullPool)
    session_maker = create_async_session_maker(engine)
    db = ImplDatabase(session_maker)
    handlers = build_handlers(queue_container)
    config = QueueExecutorConfig(
        WORKER_NAME="test-worker",
        WORKER_QUEUES=list(handlers),
        WORKER_CONCURRENCY=1,
    )
    exec_ = QueueExecutor(db=db, config=config, engine=engine, handlers=handlers)
    yield exec_
    await engine.dispose()


@pytest.fixture
async def publish(postgres_url: str) -> AsyncIterator[Callable[[BaseEvent], Awaitable[None]]]:
    engine = _create_async_engine(postgres_url, poolclass=NullPool)
    session_maker = create_async_session_maker(engine)

    async def _publish(event: BaseEvent) -> None:
        db = ImplDatabase(session_maker)
        async with session_maker() as notify_session:
            dbus = ImplDBus(db=db, session=notify_session)
            async with db:
                await dbus.publish(event)
                await db.commit()

    yield _publish
    await engine.dispose()
