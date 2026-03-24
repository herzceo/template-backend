from __future__ import annotations

from backend.internal.dto import StructDTO


class RateLimitRule(StructDTO):
    requests: int
    period: float
    unit: str = "second"

    @property
    def period_seconds(self) -> float:
        multipliers = {"second": 1.0, "minute": 60.0, "hour": 3600.0}
        return self.period * multipliers.get(self.unit, 1.0)


class RateLimiterConfig(StructDTO):
    default_rule: RateLimitRule | None = None
    endpoint_rules: dict[str, RateLimitRule] = {}  # noqa: RUF012
    strategy: str = "token_bucket"
