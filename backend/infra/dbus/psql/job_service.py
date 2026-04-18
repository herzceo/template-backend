from __future__ import annotations

from typing import TYPE_CHECKING, final

from backend.domain.entities.queue.enums import JobEventType, JobStatus
from backend.domain.entities.queue.job_event import JobEvent

if TYPE_CHECKING:
    from backend.domain.entities.queue.job import Job
    from backend.domain.repos.database import Database
    from backend.internal import Option


@final
class JobService:
    __slots__ = ("_db",)

    def __init__(self, db: Database) -> None:
        self._db = db

    async def defer(self, job: Job) -> Job:
        created = (await self._db.gateway.job.create(job)).some(
            RuntimeError("Failed to create job")
        )
        await self._db.gateway.job_event.create(
            JobEvent(job_id=created.id, type=JobEventType.DEFERRED)
        )
        return created

    async def bulk_defer(self, jobs: list[Job]) -> list[Job]:
        if not jobs:
            return []
        created = await self._db.gateway.job.bulk_create(jobs)
        await self._db.gateway.job_event.bulk_create(
            [JobEvent(job_id=j.id, type=JobEventType.DEFERRED) for j in created]
        )
        return created

    async def fetch(self, queue_names: list[str], worker_id: int) -> Option[Job]:
        result = await self._db.gateway.job.fetch_job(queue_names, worker_id)
        if result.value is not None:
            await self._db.gateway.job_event.create(
                JobEvent(job_id=result.value.id, type=JobEventType.STARTED)
            )
        return result

    async def finish(self, job: Job, status: JobStatus) -> None:
        job.status = status
        job.worker_id = None
        await self._db.gateway.job.update(job)
        await self._db.gateway.job_event.create(JobEvent(job_id=job.id, type=status))
