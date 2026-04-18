from abc import abstractmethod
from typing import Protocol

from backend.domain.entities.queue.worker import Worker


class WorkerRepo(Protocol):
    @abstractmethod
    async def register(self, name: str, queues: list[str], concurrency: int, /) -> Worker: ...

    @abstractmethod
    async def update_heartbeat(self, worker_id: int, /) -> None: ...

    @abstractmethod
    async def unregister(self, worker_id: int, /) -> None: ...
