from __future__ import annotations

import asyncio
import logging
from typing import TYPE_CHECKING

from backend.infra.database.psql.engine import create_async_engine, create_async_session_maker
from backend.infra.database.psql.repos import ImplDatabase
from backend.infra.dbus.psql.executor import HandlerDef, QueueExecutor

if TYPE_CHECKING:
    from backend.infra.database.config import DatabaseConfig
    from backend.infra.dbus.psql.config import QueueExecutorConfig

logger = logging.getLogger(__name__)


def build_handlers() -> dict[str, HandlerDef]:
    return {}


def run_queue(config: QueueExecutorConfig, db_config: DatabaseConfig) -> None:
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s %(levelname)-8s %(name)s: %(message)s",
    )
    asyncio.run(_run(config, db_config))


async def _run(config: QueueExecutorConfig, db_config: DatabaseConfig) -> None:
    engine = create_async_engine(db_config)
    session_maker = create_async_session_maker(engine)
    db = ImplDatabase(session_maker)

    executor = QueueExecutor(
        config=config,
        db=db,
        engine=engine,
        handlers=build_handlers(),
    )
    try:
        await executor.run()
    finally:
        await engine.dispose()
