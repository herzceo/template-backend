from typing import final

from sqlalchemy import func, select, text, update

from backend.domain.entities.queue.enums import JobStatus
from backend.domain.entities.queue.job import Job
from backend.domain.entities.queue.worker import Worker
from backend.domain.repos.queue.job import JobRepo
from backend.infra.database.psql.repos.base import (
    BaseRepo,
    ImplBulkCreateSupported,
    ImplCreateSupported,
    ImplGetByIdSupported,
    ImplUpdateSupported,
)
from backend.internal import Option


@final
class ImplJobRepo(
    ImplCreateSupported[Job],
    ImplBulkCreateSupported[Job],
    ImplGetByIdSupported[Job],
    ImplUpdateSupported[Job],
    JobRepo,
    BaseRepo[Job],
):
    __slots__ = ()

    async def fetch_job(self, queue_names: list[str], worker_id: int, /) -> Option[Job]:
        subq = (
            select(Job.id)
            .where(
                Job.status == JobStatus.TODO,
                Job.queue_name.in_(queue_names),
                (Job.scheduled_at.is_(None)) | (Job.scheduled_at <= func.now()),
            )
            .order_by(Job.priority.desc(), Job.id.asc())
            .limit(1)
            .with_for_update(skip_locked=True)
            .scalar_subquery()
        )

        stmt = (
            update(Job)
            .where(Job.id == subq)
            .values(
                status=JobStatus.DOING,
                worker_id=worker_id,
                attempts=Job.attempts + 1,
            )
            .returning(Job)
        )

        result = await self._session.execute(stmt)
        return Option(result.scalar_one_or_none())

    async def get_stalled(self, nb_seconds: int, /) -> list[Job]:
        stmt = (
            select(Job)
            .join(Worker, Job.worker_id == Worker.id)
            .where(
                Job.status == JobStatus.DOING,
                Worker.last_heartbeat < func.now() - text(f"interval '{nb_seconds} seconds'"),
            )
        )
        result = await self._session.execute(stmt)
        return list(result.scalars().all())
