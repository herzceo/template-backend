from __future__ import annotations

import asyncio
from fnmatch import fnmatch
from typing import TYPE_CHECKING

from backend.infra.external.http.errors import RateLimitedError
from backend.infra.external.http.sessions.middleware.rate_limit.storage import (
    InMemoryStorage,
    RateLimitStorage,
)
from backend.infra.external.http.sessions.middleware.rate_limit.strategy import (
    FixedWindowStrategy,
    RateLimitResult,
    RateLimitStrategy,
    SlidingWindowStrategy,
    TokenBucketStrategy,
)

if TYPE_CHECKING:
    from backend.infra.external.http.sessions.base import (
        HTTPResponse,
        Handler,
        Middleware,
        Request,
    )
    from backend.infra.external.http.sessions.middleware.rate_limit.config import RateLimiterConfig

type _StrategyType = TokenBucketStrategy | FixedWindowStrategy | SlidingWindowStrategy
_STRATEGY_MAP: dict[str, type[_StrategyType]] = {
    "token_bucket": TokenBucketStrategy,
    "fixed_window": FixedWindowStrategy,
    "sliding_window": SlidingWindowStrategy,
}


class RateLimiter:
    def __init__(
        self,
        config: RateLimiterConfig,
        storage: RateLimitStorage | None = None,
    ) -> None:
        self._config = config
        self._storage: RateLimitStorage = storage or InMemoryStorage()
        self._strategies: dict[str, RateLimitStrategy] = {}
        self._build_strategies()

    def _build_strategies(self) -> None:
        strategy_cls = _STRATEGY_MAP.get(self._config.strategy)
        if strategy_cls is None:
            msg = f"Unknown rate limit strategy: {self._config.strategy}"
            raise ValueError(msg)

        if self._config.default_rule is not None:
            rule = self._config.default_rule
            if strategy_cls is TokenBucketStrategy:
                self._strategies["__default__"] = TokenBucketStrategy(
                    max_tokens=rule.requests,
                    refill_rate=rule.requests / rule.period_seconds,
                )
            elif strategy_cls is FixedWindowStrategy:
                self._strategies["__default__"] = FixedWindowStrategy(
                    max_requests=rule.requests,
                    window_seconds=rule.period_seconds,
                )
            else:
                self._strategies["__default__"] = SlidingWindowStrategy(
                    max_requests=rule.requests,
                    window_seconds=rule.period_seconds,
                )

        for pattern, rule in self._config.endpoint_rules.items():
            if strategy_cls is TokenBucketStrategy:
                self._strategies[pattern] = TokenBucketStrategy(
                    max_tokens=rule.requests,
                    refill_rate=rule.requests / rule.period_seconds,
                )
            elif strategy_cls is FixedWindowStrategy:
                self._strategies[pattern] = FixedWindowStrategy(
                    max_requests=rule.requests,
                    window_seconds=rule.period_seconds,
                )
            else:
                self._strategies[pattern] = SlidingWindowStrategy(
                    max_requests=rule.requests,
                    window_seconds=rule.period_seconds,
                )

    def _resolve_strategy(self, endpoint: str) -> RateLimitStrategy | None:
        for pattern, strategy in self._strategies.items():
            if pattern != "__default__" and fnmatch(endpoint, pattern):
                return strategy
        return self._strategies.get("__default__")

    async def acquire(self, endpoint: str, identifier: str = "") -> RateLimitResult:
        strategy = self._resolve_strategy(endpoint)
        if strategy is None:
            return RateLimitResult(allowed=True)
        key = f"{endpoint}:{identifier}" if identifier else endpoint
        return await strategy.acquire(key, self._storage)


def rate_limit_middleware(limiter: RateLimiter) -> Middleware:
    def middleware(next_handler: Handler) -> Handler:
        async def handler(request: Request) -> HTTPResponse:
            result = await limiter.acquire(request.url)
            if not result.allowed:
                if result.retry_after is not None and result.retry_after > 0:
                    await asyncio.sleep(result.retry_after)
                    retry_result = await limiter.acquire(request.url)
                    if not retry_result.allowed:
                        raise RateLimitedError(
                            message=f"Rate limit exceeded: {request.url}",
                            details={"retry_after": result.retry_after},
                        )
                else:
                    raise RateLimitedError(
                        message=f"Rate limit exceeded: {request.url}",
                    )
            return await next_handler(request)

        return handler

    return middleware
