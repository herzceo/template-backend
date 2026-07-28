from typing import Protocol

from backend.internal.dto import StructDTO


class RateLimitDecision(StructDTO):
    allowed: bool
    retry_after: int


class RateLimiter(Protocol):
    """Fixed-window request counter shared across processes.

    ``hit`` records one request against ``key`` and reports whether the caller
    is still within ``limit`` for the current ``window_seconds`` window.
    """

    async def hit(self, key: str, *, limit: int, window_seconds: int) -> RateLimitDecision: ...
