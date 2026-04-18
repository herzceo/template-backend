from typing import Protocol

from backend.domain.entities.queue.worker_event import WorkerEvent
from backend.domain.repos.base import CreateSupported


class WorkerEventRepo(
    CreateSupported[WorkerEvent],
    Protocol,
): ...
