from __future__ import annotations

from typing import TYPE_CHECKING, final

from backend.domain.entities.queue.enums import WorkerEventType
from backend.domain.entities.queue.worker_event import WorkerEvent

if TYPE_CHECKING:
    from backend.app.shared.db.database import Database
    from backend.domain.entities.queue.worker import Worker


@final
class WorkerService:
    __slots__ = ("_db",)

    def __init__(self, db: Database) -> None:
        self._db = db

    async def register(self, name: str, queues: list[str], concurrency: int) -> Worker:
        worker = await self._db.gateway.queue_worker.register(name, queues, concurrency)
        await self._db.gateway.worker_event.create(
            WorkerEvent(worker_id=worker.id, type=WorkerEventType.REGISTERED)
        )
        return worker

    async def unregister(self, worker_id: int) -> None:
        await self._db.gateway.worker_event.create(
            WorkerEvent(worker_id=worker_id, type=WorkerEventType.UNREGISTERED)
        )
        await self._db.gateway.queue_worker.unregister(worker_id)

    async def heartbeat(self, worker_id: int) -> None:
        await self._db.gateway.queue_worker.update_heartbeat(worker_id)
