from prometheus_client import Counter, Gauge, Histogram

JOBS_TOTAL = Counter(
    "queue_jobs_total",
    "Total number of queue jobs processed, by queue and final status.",
    labelnames=("queue", "status"),
)

JOB_DURATION = Histogram(
    "queue_job_duration_seconds",
    "Execution time of queue jobs in seconds, by queue.",
    labelnames=("queue",),
)

JOBS_IN_PROGRESS = Gauge(
    "queue_jobs_in_progress",
    "Number of queue jobs currently executing.",
)

WORKER_UP = Gauge(
    "queue_worker_up",
    "1 while the worker is registered and sending heartbeats.",
)

__all__ = (
    "JOBS_IN_PROGRESS",
    "JOBS_TOTAL",
    "JOB_DURATION",
    "WORKER_UP",
)
