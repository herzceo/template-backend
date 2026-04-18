from typing import final

from backend.domain.entities.queue.worker_event import WorkerEvent
from backend.domain.repos.queue.worker_event import WorkerEventRepo
from backend.infra.database.psql.repos.base import BaseRepo, ImplCreateSupported


@final
class ImplWorkerEventRepo(
    ImplCreateSupported[WorkerEvent],
    WorkerEventRepo,
    BaseRepo[WorkerEvent],
):
    __slots__ = ()
