from __future__ import annotations

import time
from typing import Protocol


class RateLimitStorage(Protocol):
    async def get(self, key: str) -> dict[str, float] | None: ...

    async def set(self, key: str, value: dict[str, float], ttl: float) -> None: ...

    async def delete(self, key: str) -> None: ...


class InMemoryStorage:
    def __init__(self) -> None:
        self._data: dict[str, tuple[dict[str, float], float]] = {}

    async def get(self, key: str) -> dict[str, float] | None:
        entry = self._data.get(key)
        if entry is None:
            return None
        value, expires_at = entry
        if time.monotonic() > expires_at:
            del self._data[key]
            return None
        return value

    async def set(self, key: str, value: dict[str, float], ttl: float) -> None:
        self._data[key] = (value, time.monotonic() + ttl)

    async def delete(self, key: str) -> None:
        self._data.pop(key, None)

    def cleanup(self) -> None:
        now = time.monotonic()
        expired = [k for k, (_, exp) in self._data.items() if now > exp]
        for k in expired:
            del self._data[k]
