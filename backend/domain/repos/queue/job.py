from abc import abstractmethod
from typing import Protocol

from backend.domain.entities.queue.job import Job
from backend.domain.repos.base import (
    BulkCreateSupported,
    CreateSupported,
    GetByIdSupported,
    UpdateSupported,
)
from backend.internal import Option


class JobRepo(
    CreateSupported[Job],
    BulkCreateSupported[Job],
    GetByIdSupported[Job],
    UpdateSupported[Job],
    Protocol,
):
    @abstractmethod
    async def fetch_job(self, queue_names: list[str], worker_id: int, /) -> Option[Job]: ...

    @abstractmethod
    async def get_stalled(self, nb_seconds: int, /) -> list[Job]: ...
