from __future__ import annotations

from dataclasses import dataclass, field
from typing import final

from backend.app.shared.ports.security.rate_limiter import RateLimitDecision


@final
@dataclass
class MockRateLimiter:
    """In-memory fixed-window counter for tests.

    Permissive by default (`limit` is whatever the handler passes). Deterministic
    and process-local so a test can drive it to the throttle boundary; a fresh
    instance per container means no cross-test bleed.
    """

    _hits: dict[str, int] = field(default_factory=dict)

    async def hit(self, key: str, *, limit: int, window_seconds: int) -> RateLimitDecision:
        count = self._hits.get(key, 0) + 1
        self._hits[key] = count
        if count > limit:
            return RateLimitDecision(allowed=False, retry_after=window_seconds)
        return RateLimitDecision(allowed=True, retry_after=0)
