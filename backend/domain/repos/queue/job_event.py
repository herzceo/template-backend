from typing import Protocol

from backend.domain.entities.queue.job_event import JobEvent
from backend.domain.repos.base import BulkCreateSupported, CreateSupported


class JobEventRepo(
    CreateSupported[JobEvent],
    BulkCreateSupported[JobEvent],
    Protocol,
): ...
