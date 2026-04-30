from datetime import datetime
from typing import Any
from uuid import UUID

from backend.internal.dto import StructDTO


class AuditLog(StructDTO):
    id: UUID
    actor_id: UUID | None
    action: str
    resource_type: str
    resource_id: str
    changes: dict[str, Any] | None
    ip: str | None
    tenant_id: UUID
    created_at: datetime
