from typing import final

from backend.domain.entities.queue.job_event import JobEvent
from backend.domain.repos.queue.job_event import JobEventRepo
from backend.infra.database.psql.repos.base import (
    BaseRepo,
    ImplBulkCreateSupported,
    ImplCreateSupported,
)


@final
class ImplJobEventRepo(
    ImplCreateSupported[JobEvent],
    ImplBulkCreateSupported[JobEvent],
    JobEventRepo,
    BaseRepo[JobEvent],
):
    __slots__ = ()
