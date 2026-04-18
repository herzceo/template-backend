from enum import StrEnum


class JobStatus(StrEnum):
    TODO = "todo"
    DOING = "doing"
    SUCCEEDED = "succeeded"
    FAILED = "failed"
    CANCELLED = "cancelled"
    ABORTING = "aborting"
    ABORTED = "aborted"


class JobEventType(StrEnum):
    DEFERRED = "deferred"
    STARTED = "started"
    DEFERRED_FOR_RETRY = "deferred_for_retry"
    FAILED = "failed"
    SUCCEEDED = "succeeded"
    CANCELLED = "cancelled"
    ABORT_REQUESTED = "abort_requested"
    ABORTED = "aborted"
    SCHEDULED = "scheduled"


class WorkerEventType(StrEnum):
    REGISTERED = "registered"
    HEARTBEAT_LOST = "heartbeat_lost"
    UNREGISTERED = "unregistered"
