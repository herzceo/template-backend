from typing import final

from sqlalchemy import delete, func, update

from backend.domain.entities.queue.worker import Worker
from backend.domain.repos.queue.worker import WorkerRepo
from backend.infra.database.psql.repos.base import BaseRepo


@final
class ImplWorkerRepo(WorkerRepo, BaseRepo[Worker]):
    __slots__ = ()

    async def register(self, name: str, queues: list[str], concurrency: int, /) -> Worker:
        worker = Worker(name=name, queues=queues, concurrency=concurrency)
        self._session.add(worker)
        await self._session.flush()
        return worker

    async def update_heartbeat(self, worker_id: int, /) -> None:
        stmt = update(Worker).where(Worker.id == worker_id).values(last_heartbeat=func.now())
        await self._session.execute(stmt)

    async def unregister(self, worker_id: int, /) -> None:
        stmt = delete(Worker).where(Worker.id == worker_id)
        await self._session.execute(stmt)
