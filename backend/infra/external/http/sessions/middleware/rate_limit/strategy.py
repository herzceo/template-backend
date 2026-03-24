from __future__ import annotations

import time
from dataclasses import dataclass
from typing import TYPE_CHECKING, Protocol

if TYPE_CHECKING:
    from backend.infra.external.http.sessions.middleware.rate_limit.storage import RateLimitStorage


@dataclass(slots=True, frozen=True)
class RateLimitResult:
    allowed: bool
    retry_after: float | None = None


class RateLimitStrategy(Protocol):
    async def acquire(self, key: str, storage: RateLimitStorage) -> RateLimitResult: ...


class TokenBucketStrategy:
    def __init__(self, max_tokens: int, refill_rate: float) -> None:
        self._max_tokens = max_tokens
        self._refill_rate = refill_rate

    async def acquire(self, key: str, storage: RateLimitStorage) -> RateLimitResult:
        now = time.monotonic()
        state = await storage.get(key)

        if state is None:
            tokens = float(self._max_tokens - 1)
            await storage.set(
                key,
                {"tokens": tokens, "last_refill": now},
                ttl=self._max_tokens / self._refill_rate,
            )
            return RateLimitResult(allowed=True)

        tokens = state["tokens"]
        last_refill = state["last_refill"]
        elapsed = now - last_refill
        tokens = min(self._max_tokens, tokens + elapsed * self._refill_rate)

        if tokens < 1.0:
            retry_after = (1.0 - tokens) / self._refill_rate
            return RateLimitResult(allowed=False, retry_after=retry_after)

        tokens -= 1.0
        await storage.set(
            key,
            {"tokens": tokens, "last_refill": now},
            ttl=self._max_tokens / self._refill_rate,
        )
        return RateLimitResult(allowed=True)


class FixedWindowStrategy:
    def __init__(self, max_requests: int, window_seconds: float) -> None:
        self._max_requests = max_requests
        self._window_seconds = window_seconds

    async def acquire(self, key: str, storage: RateLimitStorage) -> RateLimitResult:
        now = time.monotonic()
        window_start = int(now // self._window_seconds) * self._window_seconds
        window_key = f"{key}:{window_start}"
        state = await storage.get(window_key)

        if state is None:
            await storage.set(
                window_key,
                {"count": 1.0, "window_start": window_start},
                ttl=self._window_seconds,
            )
            return RateLimitResult(allowed=True)

        count = int(state["count"])
        if count >= self._max_requests:
            retry_after = window_start + self._window_seconds - now
            return RateLimitResult(allowed=False, retry_after=retry_after)

        await storage.set(
            window_key,
            {"count": float(count + 1), "window_start": window_start},
            ttl=self._window_seconds,
        )
        return RateLimitResult(allowed=True)


class SlidingWindowStrategy:
    def __init__(self, max_requests: int, window_seconds: float) -> None:
        self._max_requests = max_requests
        self._window_seconds = window_seconds

    async def acquire(self, key: str, storage: RateLimitStorage) -> RateLimitResult:
        now = time.monotonic()
        window_start = now - self._window_seconds
        state = await storage.get(key)

        timestamps: list[float] = []
        if state is not None:
            timestamps = [ts for _, ts in state.items() if ts > window_start]

        if len(timestamps) >= self._max_requests:
            oldest = min(timestamps)
            retry_after = oldest + self._window_seconds - now
            return RateLimitResult(allowed=False, retry_after=max(0.0, retry_after))

        timestamps.append(now)
        encoded = {str(i): ts for i, ts in enumerate(timestamps)}
        await storage.set(key, encoded, ttl=self._window_seconds)
        return RateLimitResult(allowed=True)
