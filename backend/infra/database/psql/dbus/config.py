from backend.internal.dto import StructDTO


class QueueExecutorConfig(StructDTO):
    WORKER_NAME: str = "worker"
    WORKER_CONCURRENCY: int = 10
    WORKER_QUEUES: list[str] | None = None
    WORKER_POLL_INTERVAL: float = 5.0
    WORKER_HEARTBEAT_INTERVAL: float = 10.0
    WORKER_PERIODIC_INTERVAL: float = 60.0
    WORKER_STALLED_AFTER: int = 120
    WORKER_ABORT_POLL_INTERVAL: float = 10.0
