from __future__ import annotations

import asyncio
import contextlib
import logging
import signal as sig_mod
from datetime import UTC, datetime
from typing import TYPE_CHECKING, Any, final

from croniter import croniter
from msgspec import Struct
from sqlalchemy import text

from backend.domain.entities.queue.enums import JobStatus
from backend.domain.entities.queue.job import Job
from backend.infra.dbus.psql.job_service import JobService
from backend.infra.dbus.psql.worker_service import WorkerService

if TYPE_CHECKING:
    from collections.abc import Callable, Coroutine

    from sqlalchemy.ext.asyncio import AsyncEngine

    from backend.domain.repos.database import Database
    from backend.infra.dbus.psql.config import QueueExecutorConfig

logger = logging.getLogger(__name__)


class PeriodicConfig(Struct):
    cron: str


class HandlerDef:
    handler: Callable[..., Coroutine[Any, Any, Any]]
    periodic: PeriodicConfig | None = None
    priority: int = 0
    execution_lock: str | None = None
    queueing_lock: str | None = None


@final
class QueueExecutor:
    __slots__ = (
        "_config",
        "_db",
        "_engine",
        "_handlers",
        "_job_service",
        "_queue_names",
        "_running_tasks",
        "_semaphore",
        "_shutdown_event",
        "_wakeup_event",
        "_worker_id",
        "_worker_service",
    )

    def __init__(
        self,
        db: Database,
        config: QueueExecutorConfig,
        engine: AsyncEngine,
        handlers: dict[str, HandlerDef],
    ) -> None:
        self._config = config
        self._db = db
        self._engine = engine
        self._handlers = handlers
        self._queue_names = config.WORKER_QUEUES or list(handlers)
        self._worker_id: int = 0
        self._semaphore = asyncio.Semaphore(config.WORKER_CONCURRENCY)
        self._shutdown_event = asyncio.Event()
        self._wakeup_event = asyncio.Event()
        self._running_tasks: set[asyncio.Task[None]] = set()
        self._worker_service = WorkerService(db)
        self._job_service = JobService(db)

    async def run(self) -> None:
        self._install_signal_handlers()

        async with self._db:
            worker = await self._worker_service.register(
                self._config.WORKER_NAME,
                self._queue_names,
                self._config.WORKER_CONCURRENCY,
            )
            self._worker_id = worker.id
            await self._db.commit()

        logger.info(
            "Queue executor '%s' registered (id=%d, queues=%s, concurrency=%d)",
            self._config.WORKER_NAME,
            self._worker_id,
            self._queue_names,
            self._config.WORKER_CONCURRENCY,
        )

        loops: list[asyncio.Task[None]] = [
            asyncio.create_task(self._poll_loop()),
            asyncio.create_task(self._listen_loop()),
            asyncio.create_task(self._heartbeat_loop()),
        ]

        periodic_handlers = {
            name: hdef for name, hdef in self._handlers.items() if hdef.periodic is not None
        }
        if periodic_handlers:
            loops.append(asyncio.create_task(self._periodic_loop(periodic_handlers)))

        try:
            await asyncio.gather(*loops)
        finally:
            if self._running_tasks:
                logger.info("Waiting for %d running tasks...", len(self._running_tasks))
                await asyncio.gather(*self._running_tasks, return_exceptions=True)

            async with self._db:
                await self._worker_service.unregister(self._worker_id)
                await self._db.commit()

            logger.info("Queue executor unregistered.")

    def _install_signal_handlers(self) -> None:
        loop = asyncio.get_running_loop()
        for s in (sig_mod.SIGINT, sig_mod.SIGTERM):
            loop.add_signal_handler(s, self._handle_shutdown)

    def _handle_shutdown(self) -> None:
        logger.info("Shutdown signal received, stopping...")
        self._shutdown_event.set()
        self._wakeup_event.set()

    async def _poll_loop(self) -> None:
        while not self._shutdown_event.is_set():
            fetched = True
            while fetched and not self._shutdown_event.is_set():
                fetched = await self._try_fetch_and_run()

            self._wakeup_event.clear()
            with contextlib.suppress(TimeoutError):
                await asyncio.wait_for(
                    self._wakeup_event.wait(),
                    timeout=self._config.WORKER_POLL_INTERVAL,
                )

    async def _listen_loop(self) -> None:
        while not self._shutdown_event.is_set():
            try:
                await self._listen_for_notifications()
            except Exception:
                if self._shutdown_event.is_set():
                    return
                logger.exception("Listen loop error, reconnecting in 5s...")
                with contextlib.suppress(TimeoutError):
                    await asyncio.wait_for(
                        self._shutdown_event.wait(),
                        timeout=5.0,
                    )

    async def _listen_for_notifications(self) -> None:
        async with self._engine.connect() as conn:
            for queue in self._queue_names:
                await conn.execute(text(f"LISTEN queue_{queue}"))
            await conn.commit()

            raw = await conn.get_raw_connection()
            pgconn = raw.dbapi_connection
            if pgconn is None:
                return
            async for _ in pgconn.notifies(
                timeout=self._config.WORKER_POLL_INTERVAL,
                stop_after=None,
            ):
                self._wakeup_event.set()
                if self._shutdown_event.is_set():
                    break

    async def _heartbeat_loop(self) -> None:
        while not self._shutdown_event.is_set():
            try:
                async with self._db:
                    await self._worker_service.heartbeat(self._worker_id)
                    await self._db.commit()
            except Exception:
                logger.exception("Heartbeat update failed")

            with contextlib.suppress(TimeoutError):
                await asyncio.wait_for(
                    self._shutdown_event.wait(),
                    timeout=self._config.WORKER_HEARTBEAT_INTERVAL,
                )

    async def _periodic_loop(self, handlers: dict[str, HandlerDef]) -> None:
        while not self._shutdown_event.is_set():
            now = datetime.now(UTC)
            for queue_name, hdef in handlers.items():
                if hdef.periodic is None:
                    continue
                try:
                    await self._try_defer_periodic(queue_name, hdef, now)
                except Exception:
                    logger.exception("Failed to defer periodic job '%s'", queue_name)

            with contextlib.suppress(TimeoutError):
                await asyncio.wait_for(
                    self._shutdown_event.wait(),
                    timeout=self._config.WORKER_PERIODIC_INTERVAL,
                )

    async def _try_defer_periodic(
        self,
        queue_name: str,
        hdef: HandlerDef,
        now: datetime,
    ) -> None:
        if hdef.periodic is None:
            return
        cron = croniter(hdef.periodic.cron, now)
        next_fire: datetime = cron.get_next(datetime)

        async with self._db:
            await self._job_service.defer(
                Job(
                    queue_name=queue_name,
                    priority=hdef.priority,
                    execution_lock=hdef.execution_lock,
                    queueing_lock=f"periodic:{queue_name}",
                    scheduled_at=next_fire,
                    args={},
                )
            )
            await self._db.commit()
            logger.info("Periodic job '%s' deferred for %s", queue_name, next_fire.isoformat())

    async def _try_fetch_and_run(self) -> bool:
        if self._shutdown_event.is_set() or self._semaphore.locked():
            return False

        await self._semaphore.acquire()
        try:
            async with self._db:
                result = await self._job_service.fetch(self._queue_names, self._worker_id)
                await self._db.commit()

            if result.value is None:
                self._semaphore.release()
                return False

            job = result.value
            task = asyncio.create_task(self._execute_job(job))
            self._running_tasks.add(task)
            task.add_done_callback(self._running_tasks.discard)

        except Exception:
            self._semaphore.release()
            logger.exception("Failed to fetch job")
            return False

        return True

    async def process_one(self) -> bool:
        """Fetch and execute one job synchronously. Returns True if a job was found.

        Unlike _try_fetch_and_run, this awaits _execute_job inline (no create_task),
        making execution deterministic. Does NOT add to _running_tasks.
        """
        await self._semaphore.acquire()
        try:
            async with self._db:
                result = await self._job_service.fetch(self._queue_names, self._worker_id)
                await self._db.commit()

            if result.value is None:
                self._semaphore.release()
                return False

            job = result.value
        except Exception:
            self._semaphore.release()
            raise

        await self._execute_job(job)
        return True

    async def _execute_job(self, job: Job) -> None:
        try:
            hdef = self._handlers[job.queue_name]
            await hdef.handler(**job.args)
            status = JobStatus.SUCCEEDED
        except Exception:
            logger.exception("Job %d (queue=%s) failed", job.id, job.queue_name)
            status = JobStatus.FAILED
        finally:
            self._semaphore.release()

        async with self._db:
            await self._job_service.finish(job, status)
            await self._db.commit()
