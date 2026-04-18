from __future__ import annotations

from datetime import UTC, datetime
from typing import ClassVar

import uuid_utils
from msgspec import field

from backend.internal.dto.struct import StructDTO


def _now() -> datetime:
    return datetime.now(UTC)


class BaseEvent(StructDTO):
    name: ClassVar[str]
    id: uuid_utils.UUID = field(default_factory=uuid_utils.uuid7)
    created_at: datetime = field(default_factory=_now)
