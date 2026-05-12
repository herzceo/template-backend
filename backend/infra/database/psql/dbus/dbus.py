from __future__ import annotations

from typing import TYPE_CHECKING, final

from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession

from backend.app.shared.db.dbus import DBus, PublishOptions
from backend.domain.entities.queue.job import Job
from backend.infra.database.psql.dbus.job_service import JobService

if TYPE_CHECKING:
    from collections.abc import Sequence

    from backend.app.shared.db.database import Database
    from backend.app.shared.events import BaseEvent

_DEFAULT_OPTIONS = PublishOptions()


@final
class ImplDBus(DBus):
    __slots__ = ("_job_service", "_session")

    def __init__(self, db: Database, session: AsyncSession) -> None:
        self._job_service = JobService(db)
        self._session = session

    async def publish(
        self,
        event: BaseEvent,
        /,
        options: PublishOptions = _DEFAULT_OPTIONS,
    ) -> int:
        job = self._event_to_job(event, options)
        created = await self._job_service.defer(job)
        await self._notify(created.queue_name)
        return created.id

    async def bulk_publish(
        self,
        events: Sequence[BaseEvent],
        /,
        options: PublishOptions = _DEFAULT_OPTIONS,
    ) -> list[int]:
        jobs = [self._event_to_job(event, options) for event in events]
        created = await self._job_service.bulk_defer(jobs)

        queues_to_notify = {j.queue_name for j in created}
        for queue in queues_to_notify:
            await self._notify(queue)

        return [j.id for j in created]

    @staticmethod
    def _event_to_job(event: BaseEvent, options: PublishOptions) -> Job:
        return Job(
            queue_name=event.name,
            priority=options.priority,
            execution_lock=options.execution_lock,
            queueing_lock=options.queueing_lock,
            scheduled_at=options.scheduled_at,
            args=event.to_builtins(),
        )

    async def _notify(self, queue_name: str) -> None:
        conn = await self._session.connection()
        await conn.execute(text(f"NOTIFY queue_{queue_name}"))
